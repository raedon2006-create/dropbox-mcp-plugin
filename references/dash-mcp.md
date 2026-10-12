# Route A: Official Dropbox Dash Remote MCP

Hosted by Dropbox; no local install. Requires a Dropbox Dash plan. Read/search only — no upload, move, delete, or folder-listing tools.

## Endpoint

```
https://mcp.dropbox.com/dash
```

Authentication: Dropbox OAuth (Dynamic Client Registration for supported clients).

## Client Configuration

- **Claude Code (CLI)**: `claude mcp add --transport http DropboxDashMCP https://mcp.dropbox.com/dash`
- **Cursor**: Settings → Tools and MCP → New MCP Server:
  ```json
  { "mcpServers": { "Dropbox Dash MCP": { "url": "https://mcp.dropbox.com/dash" } } }
  ```
- **Claude Web/Desktop**: Settings → Connectors → Add custom connector → name + URL above.
- **ChatGPT Web**: Settings → Apps → Create app → URL above, Authentication: OAuth.
- **ChatGPT Codex (CLI)**: `codex mcp add DropboxDashMCP --url https://mcp.dropbox.com/dash`, then `codex mcp login DropboxDashMCP`.
- **Other MCP clients**: create a Dropbox app in the Dropbox App Console (Scoped access, Full Dropbox; permissions `account_info.read`, `dash/content.read`, `dash/content.write`; add the client's OAuth2 redirect URI), then use the App key/secret or generated access token. Generated tokens are short-lived and must be regenerated on expiry.

## Tool Reference

| Tool | Purpose |
|---|---|
| `dash_search` | Search content across all connected sources; optional filters for file type, source, source-specific labels |
| `dash_read_document` | Document metadata + optional text extraction, by UUID or URI |
| `dash_read_markdown_content` | Document content as markdown; chunked transfer for large files |
| `dash_read_binary_content` | Raw binary (images, video, audio) as base64 |
| `dash_read_visual_page` | PDF pages / slide renderings as images |
| `dash_get_sources` | List connected sources available to the user |
| `dash_get_examples` | Available filters + query examples for a source type |
| `dash_whoami` | Current user identity (display name, email) — good connectivity check |
| `dash_resolve_urls` | Resolve Dropbox/connector URLs to Dash entity UUIDs with metadata |
| `dash_list_search_actions` | List read-only search actions a source's native API exposes |
| `dash_invoke_search_action` | Execute one of those read-only search actions |

## Usage Patterns

- **Search**: start broad with `dash_search`, then refine with filters from `dash_get_examples`.
- **Find by link**: paste-URL requests → `dash_resolve_urls` first, then read by UUID.
- **Read text**: prefer `dash_read_markdown_content`; for PDFs/slides where layout matters use `dash_read_visual_page`.
- **Download to disk**: `dash_read_binary_content` (base64) → decode and save via `scripts/save_download.py --base64`.

## Limitations

- No folder listing — approximate "browsing" with `dash_search` (e.g. empty/broad query + source filter) or switch to Route B.
- Search and read only; no write operations.
- Coverage depends on which sources are connected to the user's Dash.
