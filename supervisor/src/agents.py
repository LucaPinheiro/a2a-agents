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
    model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"), temperature=0
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

    Regras de roteamento OBRIGATÓRIAS:
    - "cartao_credito": USE ESTE quando o usuário falar sobre cartões de crédito, limites, faturas, taxas, juros, benefícios, programa de pontos, dicas de uso seguro OU quando o usuário disser "quero cartão", "solicitar cartão", "pedir cartão", "cartão de crédito" ou qualquer variação sobre obter um cartão.
    - "abrir_conta": USE ESTE apenas quando o usuário falar sobre abertura de contas, tipos de conta, documentos necessários, requisitos OU quando disser "quero abrir conta", "abrir conta", "criar conta".

    IMPORTANTE: "quero cartão" ou "solicitar cartão" deve SEMPRE ir para "cartao_credito", nunca para "abrir_conta".

    Agentes disponíveis:
    - "cartao_credito"
    - "abrir_conta"

    Responda apenas em formato JSON conforme o schema abaixo.

    Pergunta do usuário: {query}
    """

    try:
        resposta = __llm.invoke(prompt)
        resultado = parser.parse(str(resposta.content))

        if isinstance(resultado, dict):
            agentes = resultado.get("agents", ["abrir_conta"])
        elif isinstance(resultado, list):
            agentes = (
                resultado
                if all(isinstance(a, str) for a in resultado)
                else ["abrir_conta"]
            )
        else:
            agentes = ["abrir_conta"]

        agentes = [a for a in agentes if a in ("cartao_credito", "abrir_conta")]
        if not agentes:
            agentes = ["abrir_conta"]

        logger.info(f"Agentes selecionados para a pergunta: {agentes}")

        return [{"query": query, "agent": agente} for agente in agentes]
    except Exception as e:
        logger.exception(f"Erro ao classificar intenção do usuário: {e}")
        return [{"query": query, "agent": "abrir_conta"}]
