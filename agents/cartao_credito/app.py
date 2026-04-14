import os
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agent.cartao_credito import run_agent

load_dotenv()

app = FastAPI(title="LG Bank - Agent Cartão de Crédito")


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "1"


@app.post("/chat")
async def chat(request: ChatRequest):
    if not request.message:
        return JSONResponse(
            status_code=400, content={"error": "Campo 'message' é obrigatório"}
        )
    try:
        resposta = await run_agent(request.message, thread_id=request.thread_id)
        return {"resposta": resposta}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
