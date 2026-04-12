from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from executor import AbrirContaExecutor


# --------------------------
# Definição do skill
# --------------------------

skill = AgentSkill(
    id="abrir_conta",
    name="Abertura de Conta MDBank",
    description="Ajuda clientes a abrir uma conta bancária e explica os tipos de contas disponíveis.",
    tags=[
        "conta",
        "abrir conta",
        "tipos de conta",
        "requisitos para abertura",
    ],
    examples=[
        "Quais são os tipos de conta disponíveis no MDBank?",
        "Como posso abrir uma conta corrente no MDBank?",
        "Quais documentos são necessários para abrir uma conta poupança?",
    ],
)

# --------------------------
# Agent Card
# --------------------------

agent_card = AgentCard(
    name="Agente de Abertura de Conta MDBank",
    description="Especialista em abertura de contas bancárias do MDBank.",
    url="http://abrir_conta_agent:8000/",
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
  agent_executor=AbrirContaExecutor(),
  task_store=InMemoryTaskStore()
)

# --------------------------
# Aplicação A2A
# --------------------------
server = A2AStarletteApplication(
  http_handler=handler,
  agent_card=agent_card
)

# Exposição do server
app = server.builder()