#!/usr/bin/env python3
"""Self-contained Dropbox MCP server: list files/folders, search, download, metadata.

Run modes:
  MCP stdio server:  python3 dropbox_mcp_server.py
  CLI (one-off):     python3 dropbox_mcp_server.py <whoami|list|search|download|metadata> ...

Auth (environment variables):
  DROPBOX_ACCESS_TOKEN                                 -> short-lived token from the App Console, OR
  DROPBOX_REFRESH_TOKEN + DROPBOX_APP_KEY + DROPBOX_APP_SECRET -> auto-refreshing OAuth (recommended)
"""
import argparse
import base64
import json
import os
import sys
import time

import requests

API = "https://api.dropboxapi.com"
CONTENT_API = "https://content.dropboxapi.com"
INLINE_DOWNLOAD_CAP = 4 * 1024 * 1024  # 4 MB; larger files must use save_to

_token_cache = {"token": None, "expires_at": 0.0}


def _access_token() -> str:
    refresh = os.environ.get("DROPBOX_REFRESH_TOKEN")
    if refresh:
        if _token_cache["token"] and time.time() < _token_cache["expires_at"] - 60:
            return _token_cache["token"]
        resp = requests.post(f"{API}/oauth2/token", data={
            "grant_type": "refresh_token",
            "refresh_token": refresh,
            "client_id": os.environ.get("DROPBOX_APP_KEY", ""),
            "client_secret": os.environ.get("DROPBOX_APP_SECRET", ""),
        }, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        _token_cache["token"] = payload["access_token"]
        _token_cache["expires_at"] = time.time() + int(payload.get("expires_in", 14400))
        return payload["access_token"]
    token = os.environ.get("DROPBOX_ACCESS_TOKEN")
    if not token:
        raise RuntimeError(
            "No credentials. Set DROPBOX_ACCESS_TOKEN, or DROPBOX_REFRESH_TOKEN "
            "+ DROPBOX_APP_KEY + DROPBOX_APP_SECRET (see references/setup.md).")
    return token


def _rpc(path: str, body: dict) -> dict:
    resp = requests.post(f"{API}{path}", json=body,
                         headers={"Authorization": f"Bearer {_access_token()}"}, timeout=60)
    _check(resp)
    return resp.json()


def _check(resp: requests.Response) -> None:
    if resp.status_code == 401:
        raise RuntimeError("Dropbox returned 401 — token invalid or expired. "
                           "Regenerate it or switch to the refresh-token flow.")
    if resp.status_code == 409:
        raise RuntimeError(f"Dropbox API error: {resp.text[:500]}")
    resp.raise_for_status()


def _fmt(entry: dict) -> dict:
    out = {"type": entry.get(".tag"), "name": entry.get("name"), "path": entry.get("path_display")}
    if entry.get(".tag") == "file":
        out.update({"size": entry.get("size"), "modified": entry.get("client_modified"),
                    "rev": entry.get("rev")})
    return out


# ---- Core operations (shared by MCP tools and CLI) ----

def whoami() -> dict:
    """Check connectivity and return the Dropbox account's name/email."""
    return _rpc("/2/users/get_current_account", {})


def list_folder(path: str = "", recursive: bool = False, max_entries: int = 2000) -> dict:
    """List files and folders. path='' is the root; use '/Folder/Sub' for subfolders."""
    result = _rpc("/2/files/list_folder",
                  {"path": path, "recursive": recursive, "limit": 2000})
    entries = [_fmt(e) for e in result["entries"]]
    while result.get("has_more") and len(entries) < max_entries:
        result = _rpc("/2/files/list_folder/continue", {"cursor": result["cursor"]})
        entries.extend(_fmt(e) for e in result["entries"])
    truncated = result.get("has_more", False)
    return {"entries": entries[:max_entries], "count": min(len(entries), max_entries),
            "truncated": truncated}


def search_files(query: str, path: str = "", max_results: int = 50) -> dict:
    """Search file/folder names and content. query is required; path narrows the scope."""
    options: dict = {"max_results": min(max_results, 1000)}
    if path:
        options["path"] = path
    result = _rpc("/2/files/search_v2", {"query": query, "options": options})
    hits = []
    for match in result.get("matches", []):
        meta = match.get("metadata", {})
        if meta.get(".tag") == "metadata":
            hits.append(_fmt(meta["metadata"]))
    return {"matches": hits, "count": len(hits), "has_more": result.get("has_more", False)}


def get_metadata(path: str) -> dict:
    """Metadata (size, modified, rev) for one file or folder."""
    return _fmt(_rpc("/2/files/get_metadata", {"path": path}))


def download_file(path: str, save_to: str | None = None) -> dict:
    """Download a file. With save_to, writes to that local path; otherwise returns
    base64 content inline (files up to 4 MB only)."""
    resp = requests.post(f"{CONTENT_API}/2/files/download",
                         headers={"Authorization": f"Bearer {_access_token()}",
                                  "Dropbox-API-Arg": json.dumps({"path": path})},
                         timeout=300)
    _check(resp)
    meta = json.loads(resp.headers.get("Dropbox-API-Result", "{}"))
    data = resp.content
    if save_to:
        directory = os.path.dirname(os.path.abspath(save_to))
        os.makedirs(directory, exist_ok=True)
        with open(save_to, "wb") as fh:
            fh.write(data)
        return {"saved_to": save_to, "bytes": len(data), "name": meta.get("name")}
    if len(data) > INLINE_DOWNLOAD_CAP:
        raise RuntimeError(f"File is {len(data)} bytes (> {INLINE_DOWNLOAD_CAP}). "
                           "Re-call with save_to to write it to disk instead.")
    return {"name": meta.get("name"), "bytes": len(data),
            "content_base64": base64.b64encode(data).decode()}


# ---- MCP server (stdio) ----

def _build_server():
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("dropbox")

    mcp.tool()(whoami)
    mcp.tool()(list_folder)
    mcp.tool()(search_files)
    mcp.tool()(get_metadata)
    mcp.tool()(download_file)
    return mcp


# ---- CLI mode ----

def _cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("whoami")
    p = sub.add_parser("list"); p.add_argument("path", nargs="?", default="")
    p.add_argument("--recursive", action="store_true"); p.add_argument("--max-entries", type=int, default=2000)
    p = sub.add_parser("search"); p.add_argument("query")
    p.add_argument("--path", default=""); p.add_argument("--max-results", type=int, default=50)
    p = sub.add_parser("metadata"); p.add_argument("path")
    p = sub.add_parser("download"); p.add_argument("path"); p.add_argument("--save-to", default=None)
    args = parser.parse_args()

    dispatch = {
        "whoami": lambda: whoami(),
        "list": lambda: list_folder(args.path, args.recursive, args.max_entries),
        "search": lambda: search_files(args.query, args.path, args.max_results),
        "metadata": lambda: get_metadata(args.path),
        "download": lambda: download_file(args.path, args.save_to),
    }
    try:
        print(json.dumps(dispatch[args.cmd](), indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI must surface any failure cleanly
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(_cli())
    _build_server().run()  # stdio MCP server
