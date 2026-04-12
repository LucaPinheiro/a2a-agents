import logging
import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.schemas import ChatRequest
from src.services import executar_supervisor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


@app.post("/chat")
async def chat_endpoint(payload: ChatRequest):
    if not payload.message:
        return JSONResponse(
            status_code=400, content={"error": "Campo 'message' é obrigatório"}
        )
    try:
        logger.info(f"Mensagem recebida no /chat: {payload.message}")
        resposta = await executar_supervisor(texto_usuario=payload.message)
        logger.info(f"Resposta gerada: {resposta}")
        return {"resposta": resposta}
    except Exception as e:
        logger.exception("Erro ao processar requisição no endpoint /chat")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/test-openai")
async def test_openai_key():
    from langchain.chat_models import init_chat_model

    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": "OPENAI_API_KEY não configurada",
                },
            )

        llm = init_chat_model(model="gpt-4o", api_key=api_key, temperature=0)
        response = llm.invoke("Responda apenas 'OK' se este teste funcionou.")

        return {
            "status": "success",
            "message": "Chave OpenAI está funcionando corretamente",
            "response": response.content,
        }
    except Exception as e:
        logger.exception("Erro ao testar chave da OpenAI")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Erro ao testar chave: {str(e)}"},
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
