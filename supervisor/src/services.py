import logging
import httpx
import operator

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from typing import TypedDict, Annotated

from src.agents import classifique_intencao_do_usuario

logger = logging.getLogger(__name__)

HTTPX_CLIENT = httpx.AsyncClient(timeout=30)

Agents = {
    "cartao_credito": "http://cartao_credito_agent:8000/chat",
    "abrir_conta": "http://abrir_conta_agent:8000/chat",
}


class State(TypedDict):
    query: str
    responses: Annotated[list[str], operator.add]


async def request_agent(message: str, agent_name: str) -> str:
    agent_url = Agents.get(agent_name)
    if not agent_url:
        return f"Erro: agente {agent_name} não encontrado"
    
    logger.info(f"Enviando mensagem para {agent_url}: {message}")
    
    try:
        response = await HTTPX_CLIENT.post(
            agent_url,
            json={"message": message},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Resposta recebida: {data}")
        
        if "resposta" in data:
            return data["resposta"]
        return str(data)
        
    except Exception as e:
        logger.error(f"Erro na requisição: {e}")
        return f"Erro ao comunicar com agente: {str(e)}"


def no_de_roteamento(state: State):
    query = state["query"]
    classificacao = classifique_intencao_do_usuario(query)

    logger.info(f"Classificação da intenção: {classificacao}")

    sends = []
    for c in classificacao:
        agent_name = c["agent"]
        logger.info(f"Roteando para agente: {agent_name}")
        sends.append(Send(agent_name, {"query": query}))

    return sends


async def cartao_credito_node(state: State):
    query = state["query"]
    resposta = await request_agent(query, "cartao_credito")
    return {"responses": [f"Resposta do agente de cartão de crédito: {resposta}"]}


async def abrir_conta_node(state: State):
    query = state["query"]
    resposta = await request_agent(query, "abrir_conta")
    return {"responses": [f"Resposta do agente de abertura de conta: {resposta}"]}


builder = StateGraph(State)
builder.add_node("cartao_credito", cartao_credito_node)
builder.add_node("abrir_conta", abrir_conta_node)
builder.add_conditional_edges(
    START, no_de_roteamento, ["cartao_credito", "abrir_conta"]
)
builder.add_edge("cartao_credito", END)
builder.add_edge("abrir_conta", END)

graph = builder.compile()


async def executar_supervisor(texto_usuario: str) -> str:
    estado_inicial: State = {"query": texto_usuario, "responses": []}
    resultado = await graph.ainvoke(estado_inicial)
    respostas = resultado["responses"]
    return "\n\n".join(respostas)
