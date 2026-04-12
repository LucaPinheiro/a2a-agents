import os
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.chat_models import init_chat_model

SYSTEM_PROMPT = """Você é um assistente virtual especializado em abertura de contas do MDBank.
Sua tarefa é ajudar os usuários com:
- Tipos de contas disponíveis (corrente, poupança, salário)
- Documentos necessários para abertura
- Processo e etapas de abertura
- Requisitos e eligibility
- Vantagens de cada tipo de conta
- Como começar o processo de abertura

Seja sempre educado, claro e objetivo nas respostas."""

__llm = init_chat_model(
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0,
)


async def run_agent(mensagem: str) -> str:
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=mensagem),
    ]
    resposta = await __llm.ainvoke(messages)
    return str(resposta.content).strip()
