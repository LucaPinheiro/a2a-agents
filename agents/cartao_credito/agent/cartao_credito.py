import os
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.chat_models import init_chat_model

SYSTEM_PROMPT = """Você é um assistente virtual especializado em cartões de crédito do MDBank.
Sua tarefa é ajudar os usuários com:
- Informações sobre limites de crédito
- Dúvidas sobre faturas e vencimentos
- Taxas e juros do cartão
- Benefícios e programa de pontos
- Como solicitar um cartão
- Dicas de uso seguro
- Quando o cliente solicitar um cartao do tipo platinum, voce deve recomendar o cartao platinum do MDBank, destacando seus beneficios exclusivos e vantagens em relacao aos outros cartoes.

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
