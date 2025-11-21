import asyncio
import os
import shlex
import sys
from typing import Dict, List

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent


def _stdio_server(command_env: str) -> Dict[str, object] | None:
    """Return a stdio MCP server config from an env var."""
    raw = os.getenv(command_env, "").strip()
    if not raw:
        return None
    parts = shlex.split(raw)
    if not parts:
        return None
    return {"transport": "stdio", "command": parts[0], "args": parts[1:]}


def _sse_server(url_env: str) -> Dict[str, object] | None:
    """Return an SSE MCP server config if provided."""
    url = os.getenv(url_env, "").strip()
    if not url:
        return None
    return {"transport": "sse", "url": url}


def build_server_config() -> Dict[str, Dict[str, object]]:
    """Configure MCP servers for Wikipedia and Wolfram Alpha."""
    servers: Dict[str, Dict[str, object]] = {}

    wikipedia_cfg = _sse_server("MCP_WIKIPEDIA_SSE_URL") or _stdio_server(
        "MCP_WIKIPEDIA_CMD"
    )
    if wikipedia_cfg:
        servers["wikipedia"] = wikipedia_cfg

    wolfram_cfg = _sse_server("MCP_WOLFRAM_SSE_URL") or _stdio_server(
        "MCP_WOLFRAM_CMD"
    )
    if wolfram_cfg:
        servers["wolfram_alpha"] = wolfram_cfg

    if not servers:
        raise RuntimeError(
            "No MCP servers configured. Set MCP_WIKIPEDIA_* or MCP_WOLFRAM_* variables."
        )

    return servers


async def load_mcp_tools() -> List[object]:
    """Load tools exposed by configured MCP servers."""
    servers = build_server_config()
    client = MultiServerMCPClient(servers)
    tools = await client.get_tools()
    print(f"Loaded {len(tools)} MCP tools: {[tool.name for tool in tools]}")
    return tools


async def main() -> int:
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required.")

    try:
        tools = await load_mcp_tools()
    except Exception as exc:  # noqa: BLE001
        print(
            f"Failed to load MCP tools: {exc}\n"
            "Check MCP_WIKIPEDIA_CMD / MCP_WOLFRAM_CMD (or SSE URLs) and ensure the commands exist."
        )
        return 1

    if not tools:
        print(
            "No MCP tools loaded. Set MCP_WIKIPEDIA_CMD / MCP_WOLFRAM_CMD or their SSE URLs."
        )
        return 1
    model = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"), temperature=0
    )

    prompt = (
        "You are a world-knowledge analyst. "
        "Use the MCP tools to ground your answers: Wikipedia for factual context "
        "and Wolfram Alpha for math/science queries. "
        "Explain which tool you called and keep replies concise."
    )
    agent = create_react_agent(model=model, tools=tools, prompt=prompt)

    print("Ask about the world (type 'exit' to quit).")
    while True:
        user_text = input("User> ").strip()
        if user_text.lower() in {"exit", "quit", "q"}:
            break

        try:
            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=user_text)]},
                {"recursion_limit": 12},
            )
            final_message = result["messages"][-1].content
            print(f"Assistant> {final_message}")
        except Exception as exc:  # noqa: BLE001
            print(f"Error while processing your request: {exc}")
            continue


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
