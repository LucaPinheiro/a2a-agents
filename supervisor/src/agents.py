import logging
import os
from typing import List

from langchain_core.messages import HumanMessage
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

logger = logging.getLogger(__name__)

__llm = init_chat_model(
    model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"), temperature=0
)


class RouterOutput(BaseModel):
    agents: List[str] = Field(
        ...,
        description="Lista de agentes disponíveis para responder a pergunta do usuário",
    )


parser = JsonOutputParser(pydantic_object=RouterOutput)


def classifique_intencao_do_usuario(query: str) -> List[dict]:
    prompt = f"""
    Analise a pergunta do usuário e classifique quais agentes devem responder.
    
    Agentes disponíveis:
    - "cartao_credito": para perguntas sobre cartões de crédito, taxas, limites, faturas
    - "abrir_conta": para perguntas sobre abertura de contas, tipos de conta, requisitos
    
    Responda apenas em formato JSON conforme o schema abaixo.
    
    Pergunta do usuário: {query}
    """

    try:
        resposta = __llm.invoke(prompt)
        resultado = parser.parse(str(resposta.content))

        agentes = resultado.get("agents", ["abrir_conta"])
        logger.info(f"Agentes selecionados para a pergunta: {agentes}")

        return [{"query": query, "agent": agente} for agente in agentes]
    except Exception as e:
        logger.exception(f"Erro ao classificar intenção do usuário: {e}")
        return [{"query": query, "agent": "abrir_conta"}]
