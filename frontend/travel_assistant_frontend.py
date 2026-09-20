"""Streamlit UI for the Singapore Travel Planning Assistant."""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.travel_assistant_backend import TravelAssistant

st.set_page_config(page_title="Singapore Travel Assistant", layout="wide")

st.title("Singapore Travel Planning Assistant")
st.caption(
    "Destination knowledge from travel guides (RAG) + live weather & currency (MCP tools)"
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "assistant" not in st.session_state:
    with st.spinner("Loading..."):
        try:
            st.session_state.assistant = TravelAssistant()
        except ValueError as e:
            st.error(str(e))
            st.info("Set GOOGLE_API_KEY in a config.py file and restart the app.")
            st.stop()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("Knowledge Base Sources"):
                for s in msg["sources"]:
                    st.markdown(f"- [{s['title']}]({s['url']})")
        if msg.get("tools_used"):
            st.caption(f"MCP tools used: {', '.join(msg['tools_used'])}")

if prompt := st.chat_input("Ask about Singapore travel..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Planning..."):
            result = st.session_state.assistant.chat(prompt, st.session_state.history)

        st.markdown(result["response"])

        if result["sources"]:
            with st.expander("Knowledge Base Sources"):
                for s in result["sources"]:
                    st.markdown(f"- [{s['title']}]({s['url']})")

        if result["tools_used"]:
            st.caption(f"MCP tools used: {', '.join(result['tools_used'])}")

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["response"],
            "sources": result["sources"],
            "tools_used": result["tools_used"],
        }
    )
    st.session_state.history.append({"user": prompt, "assistant": result["response"]})


if hasattr(st.session_state, "_pending_prompt"):
    prompt = st.session_state._pending_prompt
    del st.session_state._pending_prompt
    st.session_state.messages.append({"role": "user", "content": prompt})
    result = st.session_state.assistant.chat(prompt, st.session_state.history)
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["response"],
            "sources": result["sources"],
            "tools_used": result["tools_used"],
        }
    )
    st.session_state.history.append({"user": prompt, "assistant": result["response"]})
    st.rerun()
