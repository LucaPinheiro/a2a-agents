from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from executor import CartaoCreditoExecutor


# --------------------------
# Definição do skill
# --------------------------

skill = AgentSkill(
    id="cartao_credito",
    name="Cartão de Crédito MDBank",
    description="Ajuda clientes com informações sobre cartões de crédito, taxas, limites e benefícios.",
    tags=[
        "cartão",
        "cartão de crédito",
        "limite",
        "fatura",
        "taxas",
        "benefícios",
    ],
    examples=[
        "Qual é o limite do meu cartão de crédito?",
        "Como funciona a fatura do cartão MDBank?",
        "Quais são os benefícios do cartão de crédito?",
        "Quais as taxas do cartão de crédito?",
    ],
)

# --------------------------
# Agent Card
# --------------------------

agent_card = AgentCard(
    name="Agente de Cartão de Crédito MDBank",
    description="Especialista em cartões de crédito do MDBank.",
    url="http://cartao_credito_agent:8000/",
    default_input_modes=["text"],
    default_output_modes=["text"],
    skills={skill},
    version="1.0.0",
    capabilities=AgentCapabilities(),
)

# --------------------------
# Request Handler
# --------------------------

handler = DefaultRequestHandler(
    agent_executor=CartaoCreditoExecutor(), task_store=InMemoryTaskStore()
)

# --------------------------
# Aplicação A2A
# --------------------------
server = A2AStarletteApplication(http_handler=handler, agent_card=agent_card)

# Exposição do server
app = server.builder()
