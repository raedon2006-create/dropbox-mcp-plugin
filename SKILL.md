---
name: dropbox-mcp
description: >-
  Browse, search, and download files from a Dropbox account via a bundled, self-contained MCP server. Use when the user asks to list Dropbox files or folders, search Dropbox, download a file from Dropbox, connect Dropbox to an MCP client (Claude, Cursor, Codex, ChatGPT), or set up a Dropbox MCP plugin/server. Ships a ready-to-run server (scripts/dropbox_mcp_server.py) with both MCP stdio and CLI modes, plus an OAuth helper. Also documents the official Dropbox Dash remote MCP (https://mcp.dropbox.com/dash) as a hosted, search-only alternative.
---

# Dropbox MCP

## Overview

This skill bundles a working Dropbox MCP server. It needs only a Dropbox access token (or refresh token) and Python 3.10+ — no third-party server to install. Use it to list files/folders, search, read metadata, and download files from the user's Dropbox.

## Quick Start

1. Get credentials (one-time, user does this): see [references/setup.md](references/setup.md) — create a Dropbox app with scopes `files.metadata.read`, `files.content.read`, `account_info.read`, then either generate an access token or run `scripts/get_refresh_token.py` for a long-lived refresh token.
2. Install deps: `pip install -r scripts/requirements.txt`.
3. Verify connectivity: `DROPBOX_ACCESS_TOKEN=... python3 scripts/dropbox_mcp_server.py whoami`.

## Use It Two Ways

### CLI mode (fastest for one-off agent tasks)

```bash
python3 scripts/dropbox_mcp_server.py list "/Documents"          # browse a folder ("" = root)
python3 scripts/dropbox_mcp_server.py list "" --recursive        # whole tree
python3 scripts/dropbox_mcp_server.py search "invoice" --path "/Documents"
python3 scripts/dropbox_mcp_server.py metadata "/Reports/q3.pdf"
python3 scripts/dropbox_mcp_server.py download "/Reports/q3.pdf" --save-to ./q3.pdf
```

All output is JSON on stdout; failures print `{"error": ...}` on stderr with exit code 1.

### MCP stdio server (register in a client)

Run with no arguments. Client config (Claude Desktop/Cursor style):

```json
{
  "mcpServers": {
    "dropbox": {
      "command": "python3",
      "args": ["/path/to/scripts/dropbox_mcp_server.py"],
      "env": { "DROPBOX_ACCESS_TOKEN": "<token>" }
    }
  }
}
```

Tools exposed: `whoami`, `list_folder`, `search_files`, `get_metadata`, `download_file`.

## Operational Notes

- Dropbox paths use forward slashes with a leading `/` (`/Docs/a.pdf`); root is the empty string `""`.
- `download_file` without `save_to` returns base64 inline but refuses files > 4 MB — always pass `save_to` for binary downloads; decode small inline payloads with `scripts/save_download.py --base64` if needed.
- Generated access tokens from the App Console expire after ~4 hours. For anything recurring, use the refresh-token env vars (`DROPBOX_REFRESH_TOKEN` + `DROPBOX_APP_KEY` + `DROPBOX_APP_SECRET`) — the server refreshes automatically.
- 401 means expired/invalid token: regenerate or switch to the refresh flow. 409 with `path/not_found` means wrong path (check casing).
- Before overwriting a local file with a download, confirm the target path with the user.

## Alternative: Official Dash Remote MCP

If the user has Dropbox Dash and only needs search + content reading (no folder browsing or true downloads), the hosted server at `https://mcp.dropbox.com/dash` requires no local setup. See [references/dash-mcp.md](references/dash-mcp.md).

## Resources

- `scripts/dropbox_mcp_server.py` — the MCP server (stdio) + CLI. Deps: `scripts/requirements.txt`.
- `scripts/get_refresh_token.py` — one-time OAuth helper for a long-lived refresh token.
- `scripts/save_download.py` — save base64/text payloads to disk.
- `references/setup.md` — Dropbox app creation, scopes, token options, client configs, troubleshooting.
- `references/dash-mcp.md` — official hosted Dash MCP: endpoint, per-client config, tool reference, limitations.
