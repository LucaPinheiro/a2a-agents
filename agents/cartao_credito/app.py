import os
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from langchain_core.messages import HumanMessage, SystemMessage
from langchain.chat_models import init_chat_model

load_dotenv()

app = FastAPI(title="LG Bank - Agent Cartão de Crédito")

__llm = init_chat_model(
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0,
)

SYSTEM_PROMPT = """Você é um assistente virtual especializado em cartões de crédito. 
Sua tarefa é ajudar os usuários a entenderem melhor seus cartões de crédito, 
responder perguntas sobre taxas, prazos e benefícios, e fornecer informações úteis."""


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
async def chat(request: ChatRequest):
    if not request.message:
        return JSONResponse(
            status_code=400, content={"error": "Campo 'message' é obrigatório"}
        )
    try:
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=request.message),
        ]
        resposta = await __llm.ainvoke(messages)
        return {"resposta": str(resposta.content).strip()}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
