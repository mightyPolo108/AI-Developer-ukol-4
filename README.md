# MCP world reasoner

LangGraph agent that routes questions to MCP tools for Wikipedia (facts) and Wolfram Alpha (math/physics).

## Prerequisites
- `OPENAI_API_KEY` in your env (and optionally `OPENAI_MODEL`, defaults to `gpt-4.1-mini`)
- MCP servers available locally (no hardcoded defaults):
  - Set `MCP_WIKIPEDIA_CMD` to a runnable Wikipedia MCP server (e.g., `npx -y @shelm/wikipedia-mcp-server`) **or** set `MCP_WIKIPEDIA_SSE_URL` to an existing SSE endpoint.
  - Set `MCP_WOLFRAM_CMD` to a runnable Wolfram MCP server **or** set `MCP_WOLFRAM_SSE_URL` to an existing SSE endpoint. You also need `WOLFRAM_ALPHA_APPID` if that server requires it.
  - Set `MCP_WHOIS_CMD` to a WHOIS MCP server (e.g., `npx -y @modelcontextprotocol/server-whois`) **or** set `MCP_WHOIS_SSE_URL` to an existing SSE endpoint.

If the npm package you try (e.g., `@modelcontextprotocol/server-wolfram-alpha`) is not on the registry, use a local clone/binary or an SSE URL instead.

## Install
```bash
cd 8-langgraph/5_agent/3_mcp_world_reasoner
uv sync  # or: pip install .
```

## Run
Start any required MCP servers (or let the stdio commands above be spawned automatically), then:
```bash
python main.py
```
Example query:
```
User> How many moons does Mars have and what was the global population in 1950?
```
The agent will call Wikipedia/Wolfram tools via MCP and return a grounded answer.
