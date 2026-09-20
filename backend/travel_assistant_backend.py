import asyncio
import sys
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

from backend.config import GEMINI_MODEL, GOOGLE_API_KEY, MCP_SERVERS_DIR
from backend.prompts import SYSTEM_PROMPT
from backend.rag import load_vector_store, retrieve

PYTHON = sys.executable


class TravelAssistant:
    def __init__(self):
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable is required.")
        self.llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=0.3,
            thinking_budget=0,
        )
        self.vector_store = load_vector_store()
        self._agent = None
        self._mcp_client = None

    def _mcp_config(self) -> dict:
        return {
            "weather": {
                "transport": "stdio",
                "command": PYTHON,
                "args": [str(MCP_SERVERS_DIR / "weather_server.py")],
            },
            "currency": {
                "transport": "stdio",
                "command": PYTHON,
                "args": [str(MCP_SERVERS_DIR / "currency_server.py")],
            },
        }

    async def _ensure_agent(self):
        if self._agent is not None:
            return

        self._mcp_client = MultiServerMCPClient(self._mcp_config())
        tools = await self._mcp_client.get_tools()
        self._agent = create_react_agent(self.llm, tools)

    def _format_sources(self, sources: list[dict]) -> str:
        if not sources:
            return "No knowledge base sources retrieved."
        lines = []
        for s in sources:
            lines.append(f"- {s['title']}: {s['url']}")
        return "\n".join(lines)

    def _extract_tool_calls(self, messages: list) -> list[str]:
        tools_used = []
        for msg in messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tools_used.append(tc.get("name", "unknown"))
        return tools_used

    async def chat_async(self, user_message: str, history: list[dict]) -> dict:
        await self._ensure_agent()

        context, sources = retrieve(user_message, self.vector_store)
        system_content = SYSTEM_PROMPT.format(
            context=context or "No relevant content found in knowledge base.",
            sources=self._format_sources(sources),
        )

        messages = [SystemMessage(content=system_content)]
        for turn in history:
            messages.append(HumanMessage(content=turn["user"]))
            messages.append(AIMessage(content=turn["assistant"]))

        messages.append(HumanMessage(content=user_message))

        try:
            result = await self._agent.ainvoke({"messages": messages})
            response_messages = result.get("messages", [])
            ai_response = response_messages[-1].content if response_messages else "No response generated."
            tools_used = self._extract_tool_calls(response_messages)
        except Exception as e:
            ai_response = f"Sorry, I encountered an error: {e}"
            tools_used = []

        return {
            "response": ai_response,
            "sources": sources,
            "tools_used": tools_used,
        }

    def chat(self, user_message: str, history: list[dict]) -> dict:
        return asyncio.run(self.chat_async(user_message, history))
