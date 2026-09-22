"""
Streamlit frontend entry point.

This app NEVER imports groq or holds GROQ_API_KEY. It only knows about
BACKEND_URL, and talks to the FastAPI backend exclusively over HTTP.
"""

import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# Fixed model for this project -- the backend also only supports this one
# (see SUPPORTED_MODELS in app/services/llm_service.py on the backend).
MODEL = "openai/gpt-oss-120b"

st.title("LLM Chat")

use_streaming = st.checkbox("Stream response", value=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("Type your message...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    request_body = {"message": user_input, "model": MODEL}

    with st.chat_message("assistant"):
        if use_streaming:
            try:
                def stream_chunks():
                    with requests.post(
                        f"{BACKEND_URL}/api/v1/chat/stream",
                        json=request_body,
                        stream=True,
                        timeout=60,
                    ) as resp:
                        resp.raise_for_status()
                        for chunk in resp.iter_content(chunk_size=None, decode_unicode=True):
                            if chunk:
                                yield chunk

                reply = st.write_stream(stream_chunks)
            except requests.exceptions.HTTPError as exc:
                reply = f"Backend returned an error: {exc.response.status_code} — {exc.response.text}"
                st.error(reply)
            except requests.exceptions.RequestException as exc:
                reply = f"Could not reach backend: {exc}"
                st.error(reply)
        else:
            with st.spinner("Thinking..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/api/v1/chat",
                        json=request_body,
                        timeout=60,
                    )
                    response.raise_for_status()
                    reply = response.json()["response"]
                    st.write(reply)
                except requests.exceptions.HTTPError as exc:
                    reply = f"Backend returned an error: {exc.response.status_code} — {exc.response.text}"
                    st.error(reply)
                except requests.exceptions.RequestException as exc:
                    reply = f"Could not reach backend: {exc}"
                    st.error(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})