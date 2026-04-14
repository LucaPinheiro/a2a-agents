import os
from langchain_core.messages import HumanMessage
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent

__llm = init_chat_model(
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.3,
)

client = MultiServerMCPClient(
    {
        "conta": {
            "transport": "http",
            "url": "http://recursos:8000/mcp_gateway",
        }
    }
)

memory = InMemorySaver()


async def build_agent():
    tools = await client.get_tools()

    agent = create_react_agent(
        model=__llm,
        tools=tools,
        prompt=(
            "Você é um assistente virtual especializado em cartões de crédito do MDBank.\n\n"
            "Fluxo obrigatório:\n"
            "1. SEMPRE valide se o cliente possui conta antes de falar sobre cartão de crédito.\n"
            "   - Use consultar_conta para verificar.\n"
            "   - Se não existir conta:\n"
            "     -> informe que é necessário ter uma conta primeiro\n"
            "     -> ofereça abrir uma conta (use gerar_prompt_abertura e depois criar_ou_buscar_conta se o cliente aceitar)\n"
            "     -> só depois de criada a conta, prossiga com o cartão\n\n"
            "2. Se já existir conta (ou após criar):\n"
            "   - Você pode ajudar com:\n"
            "     * Informações sobre limites de crédito\n"
            "     * Dúvidas sobre faturas e vencimentos\n"
            "     * Taxas e juros do cartão\n"
            "     * Benefícios e programa de pontos\n"
            "     * Como solicitar um cartão\n"
            "     * Dicas de uso seguro\n"
            "   - Quando o cliente solicitar um cartão do tipo platinum, recomende o cartão platinum do MDBank, destacando seus benefícios exclusivos e vantagens em relação aos outros cartões.\n"
            "   - Se o cliente quiser solicitar o cartão, use solicitar_cartao.\n\n"
            "Regras:\n"
            "- Nunca invente dados\n"
            "- Sempre use tools para decisões reais\n"
            "- Use mensagens claras para o cliente\n"
            "- Seja sempre educado, claro e objetivo\n"
        ),
        checkpointer=memory,
    )
    return agent


async def run_agent(mensagem: str, thread_id: str = "1") -> str:
    agent = await build_agent()
    response = await agent.ainvoke(
        {"messages": [HumanMessage(content=mensagem)]},
        {"configurable": {"thread_id": thread_id}},
    )
    return response["messages"][-1].content
