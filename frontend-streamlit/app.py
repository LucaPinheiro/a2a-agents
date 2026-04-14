import os
import uuid

import requests
import streamlit as st

SUPERVISOR_URL = os.getenv("SUPERVISOR_URL", "http://supervisor:8000/chat")

st.set_page_config(page_title="LG Bank", page_icon="🏦")

st.title("🏦 LG Bank - Assistente Virtual")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "client_id" not in st.session_state:
    st.session_state.client_id = str(uuid.uuid4())

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Digite sua mensagem...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                response = requests.post(
                    SUPERVISOR_URL,
                    json={
                        "message": user_input,
                        "session_id": st.session_state.session_id,
                        "client_id": st.session_state.client_id,
                    },
                    timeout=60,
                )
                response.raise_for_status()
                data = response.json()
                resposta = data.get("resposta", "Sem resposta do supervisor.")
            except requests.exceptions.RequestException as e:
                resposta = f"Erro ao comunicar com o supervisor: {e}"

        st.markdown(resposta)

    st.session_state.messages.append({"role": "assistant", "content": resposta})
