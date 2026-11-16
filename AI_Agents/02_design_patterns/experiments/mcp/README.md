# MCP — Agent + an existing filesystem MCP server

`agent --(MCP over stdin/stdout)--> @modelcontextprotocol/server-filesystem (npx) --> 02_design_patterns/`

## Run 1 (2026-11-16)
- Server tools after `tool_filter`: `directory_tree, list_directory, read_text_file, search_files`, no write tools ✅
- 5 calls: 1 `search_files("**/README.md")` + 4 `read_text_file`. It planned search → read on its own.
- The answer summarized all 4 pattern READMEs correctly.

## Setup gotcha
`ImportError: cannot import name 'McpToolset'` = **`mcp` not installed in the venv**. ADK hides the real error (try/except in `mcp_tool/__init__.py`).
The venv was made by **uv → it has no pip**, so a bare `pip install` went into a global Python. Use `uv pip install mcp` / `python -m pip`.

## Python tool vs MCP server
| | Python function tool | MCP server |
|---|---|---|
| Who writes it | Us | Usually someone else (or us, to share) |
| Reuse | This agent/framework | Any MCP client: ADK, Claude, IDEs |
| Transport | In-process | stdio (local) or HTTP (remote) |
| Control | Full, change anytime | Their code, their updates |
| Choose when | Logic specific to us / needs tight control | Reusing existing integrations, or sharing ours with other teams |

## Risks & guardrails
- A server is **someone else's code running with our permissions**; `npx -y` pulls the **latest** version each run → supply-chain risk → **pin the version**, use trusted servers.
- Tool descriptions come from the server → a malicious server can **inject instructions** into the prompt.
- `tool_filter` hides tools from the model; the **real boundary is the allowed folder** (+ OS permissions).
- Phase 1 loop limits still apply (max 15 LLM calls, 120s timeout).
