# Setup: Credentials and Client Configuration

The bundled server (`scripts/dropbox_mcp_server.py`) talks to the official Dropbox HTTP API. The user must create their own Dropbox app — never share or hardcode someone else's credentials.

## 1. Create a Dropbox App (one-time)

1. Go to the Dropbox App Console → **Create app**.
2. **API:** Scoped access. **Access:** Full Dropbox (or App folder to sandbox it). Pick a unique name.
3. **Permissions tab** — enable:
   - `account_info.read` (whoami check)
   - `files.metadata.read` (list/search/metadata)
   - `files.content.read` (download)
   - Optional, only if write features are added later: `files.content.write`, `sharing.write`.

## 2. Choose a Token Strategy

### Option A: Generated access token (quick tests only)

App Console → Settings → **Generate access token** → set:

```bash
export DROPBOX_ACCESS_TOKEN=sl.xxxx
```

Expires in ~4 hours; a 401 means regenerate.

### Option B: Refresh token (recommended, never expires)

In the App Console, add OAuth2 redirect URI `http://localhost` (not strictly needed for the copy-paste code flow), then run:

```bash
python3 scripts/get_refresh_token.py --app-key <key> --app-secret <secret>
```

Approve in the browser, paste the code, then set:

```bash
export DROPBOX_REFRESH_TOKEN=xxxx
export DROPBOX_APP_KEY=xxxx
export DROPBOX_APP_SECRET=xxxx
```

The server exchanges and caches short-lived tokens automatically.

## 3. Register as an MCP Server

Claude Code CLI:

```bash
claude mcp add dropbox -- python3 /path/to/scripts/dropbox_mcp_server.py
# add env vars in the client's config if not exported globally
```

Claude Desktop / Cursor (`claude_desktop_config.json` / Cursor MCP settings):

```json
{
  "mcpServers": {
    "dropbox": {
      "command": "python3",
      "args": ["/absolute/path/to/scripts/dropbox_mcp_server.py"],
      "env": {
        "DROPBOX_REFRESH_TOKEN": "<refresh token>",
        "DROPBOX_APP_KEY": "<app key>",
        "DROPBOX_APP_SECRET": "<app secret>"
      }
    }
  }
}
```

Restart the client after editing config. Verify with: "Use the dropbox whoami tool."

## 4. Tool Reference (bundled server)

| Tool | Args | Notes |
|---|---|---|
| `whoami` | — | Connectivity check; returns account name/email |
| `list_folder` | `path=""`, `recursive=false`, `max_entries=2000` | Paginates automatically; `truncated` flag if capped |
| `search_files` | `query`, `path=""`, `max_results=50` | Name + content search (content search depends on plan) |
| `get_metadata` | `path` | Size, modified, rev |
| `download_file` | `path`, `save_to=null` | Inline base64 ≤4 MB, otherwise requires `save_to` |

CLI equivalents: `whoami`, `list`, `search`, `metadata`, `download` (same arguments as flags).

## 5. Troubleshooting

- **401** — expired/invalid token; regenerate or switch to Option B.
- **409 `path/not_found`** — wrong path or casing; paths need a leading `/`.
- **409 `insufficient_permissions`** — missing scope; enable it in the Permissions tab, then re-auth (new token).
- **Dropbox Business team spaces** — content may live under a team root; browse from `""` first.
- **`ModuleNotFoundError: mcp`** — run `pip install -r scripts/requirements.txt`; pin is `mcp>=1.2,<2` (v2 renamed FastMCP).
