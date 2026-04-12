import logging
import uuid
import httpx
import operator

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from typing import TypedDict, Annotated

from a2a.client import A2ACardResolver, ClientFactory, ClientConfig
from a2a.types import Message, Part, Role, TextPart

from src.agents import classifique_intencao_do_usuario

logger = logging.getLogger(__name__)

HTTPX_CLIENT = httpx.AsyncClient(timeout=30)

Agents = {
    "cartao_credito": "http://cartao_credito_agent:8000",
    "abrir_conta": "http://abrir_conta_agent:8000",
}

CLIENT_CACHE = {}


class State(TypedDict):
    query: str
    responses: Annotated[list[str], operator.add]


async def request_agent(message: str, agent_name: str) -> str:
    agent_url = Agents.get(agent_name)
    if not agent_url:
        return f"Erro: agente {agent_name} não encontrado"

    if agent_url not in CLIENT_CACHE:
        logger.info(f"Instanciando cliente para o agente {agent_url}")
        resolver = A2ACardResolver(HTTPX_CLIENT, agent_url)

        try:
            agent_card = await resolver.get_agent_card()
            logger.info(
                f"Agent encontrado: {agent_card.name} - {agent_card.description}"
            )
        except Exception as e:
            logger.error(f"Erro ao obter agent card: {e}")
            return f"Erro: não foi possível conectar ao agente {agent_name}"

        config = ClientConfig(httpx_client=HTTPX_CLIENT, streaming=False)

        factory = ClientFactory(config)
        CLIENT_CACHE[agent_url] = factory.create_client(agent_card)

    client = CLIENT_CACHE[agent_url]

    msg = Message(
        role=Role.user,
        message_id=str(uuid.uuid4()),
        parts=[Part(root=TextPart(text=message))],
    )

    logger.info(f"Enviando mensagem para o agente {agent_name}: {message}")

    try:
        async for event in client.send_message(msg):
            if isinstance(event, Message):
                for part in event.parts:
                    if part.root.kind == "text":
                        resposta = part.root.text
                        logger.info(
                            f"Resposta recebida do agente {agent_name}: {resposta}"
                        )
                        return resposta
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem: {e}")
        return f"Erro ao comunicar com agente: {str(e)}"

    return "Erro: resposta inválida do agente"


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


def cartao_credito_node(state: State):
    query = state["query"]
    resposta = request_agent(query, "cartao_credito")
    return {"responses": [f"Resposta do agente de cartão de crédito: {resposta}"]}


def abrir_conta_node(state: State):
    query = state["query"]
    resposta = request_agent(query, "abrir_conta")
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
