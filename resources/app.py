import json
import os
import random
import re
from typing import Any, Dict, Optional
from urllib.parse import quote

from fastmcp import FastMCP, Context
from fastmcp.prompts import Message

mcp = FastMCP("MDBank Recursos")

DB_FILE = "/app/db.json"


def load_db() -> Dict[str, Any]:
    if not os.path.exists(DB_FILE):
        return {"contas": {}, "cartoes": {}}
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"contas": {}, "cartoes": {}}


def save_db():
    try:
        with open(DB_FILE, "w") as f:
            json.dump({"contas": contas_mdbank, "cartoes": cartoes_mdbank}, f, indent=2)
    except Exception as e:
        print("Erro ao salvar DB:", e)


def extract_resource_data(resource_result) -> Optional[Dict[str, Any]]:
    if not resource_result:
        return None
    try:
        if not resource_result.contents:
            return None
        raw = resource_result.contents[0].content
        if isinstance(raw, str):
            return json.loads(raw)
        return raw
    except Exception as e:
        print("Erro extract_resource_data:", e)
        return None


def _sanitize_cpf(cpf: str) -> str:
    cpf = cpf.strip()
    cpf = re.sub(r"[^0-9]", "", cpf)
    return cpf if cpf else "invalido"


db = load_db()
contas_mdbank: Dict[str, Any] = db.get("contas", {})
cartoes_mdbank: Dict[str, Any] = db.get("cartoes", {})


@mcp.resource("conta://{cpf}")
async def obter_conta(cpf: str):
    cpf = _sanitize_cpf(cpf)
    data = contas_mdbank.get(cpf, {"erro": "Conta não encontrada"})
    return json.dumps(data)


@mcp.resource("cartao://{cpf}")
async def obter_cartao(cpf: str):
    cpf = _sanitize_cpf(cpf)
    data = cartoes_mdbank.get(cpf, {"erro": "Cartão não encontrado"})
    return json.dumps(data)


@mcp.prompt()
def abrir_conta_prompt(nome: str, cpf: str):
    return [
        Message("O cliente deseja abrir conta."),
        Message(f"Nome: {nome} | CPF: {cpf}"),
        Message("Verifique se já existe conta antes de criar.", role="assistant"),
    ]


@mcp.prompt()
def solicitar_cartao_prompt(cpf: str, tipo: str):
    return [
        Message(f"Cliente quer cartão {tipo}"),
        Message(f"CPF: {cpf}"),
        Message("Verifique se possui conta antes de emitir cartão.", role="assistant"),
    ]


@mcp.tool()
async def consultar_conta(cpf: str, ctx: Context) -> dict:
    """Consulta se o cliente possui conta no MDBank."""
    cpf = _sanitize_cpf(cpf)
    resource = await ctx.read_resource(f"conta://{quote(cpf, safe='')}")
    print("\n ==================== \n", resource, "\n ========================= \n")
    data = extract_resource_data(resource)
    if not data or "erro" in data:
        return {"existe": False}
    return {"existe": True, "conta": data}


@mcp.tool()
async def consultar_cartao(cpf: str, ctx: Context) -> dict:
    """Consulta se o cliente possui cartão no MDBank."""
    cpf = _sanitize_cpf(cpf)
    resource = await ctx.read_resource(f"cartao://{quote(cpf, safe='')}")
    data = extract_resource_data(resource)
    if not data or "erro" in data:
        return {"existe": False}
    return {"existe": True, "cartao": data}


@mcp.tool()
async def criar_ou_buscar_conta(nome: str, cpf: str, ctx: Context) -> dict:
    """Cria uma nova conta ou retorna a existente para o cliente."""
    cpf = _sanitize_cpf(cpf)
    await ctx.info(f"[Conta] Processando CPF {cpf}")
    resource = await ctx.read_resource(f"conta://{quote(cpf, safe='')}")
    data = extract_resource_data(resource)
    if data and "erro" not in data:
        return {"status": "existente", "conta": data}

    numero_conta = random.randint(10000, 99999)
    conta = {
        "nome": nome,
        "numero": numero_conta,
        "saldo": 0.0,
    }
    contas_mdbank[cpf] = conta
    save_db()

    return {"status": "criada", "conta": conta}


@mcp.tool()
async def solicitar_cartao(cpf: str, tipo: str, ctx: Context) -> dict:
    """Solicita um cartão de crédito para o cliente."""
    cpf = _sanitize_cpf(cpf)
    resource_conta = await ctx.read_resource(f"conta://{quote(cpf, safe='')}")
    conta_data = extract_resource_data(resource_conta)
    if not conta_data or "erro" in conta_data:
        return {"status": "erro", "mensagem": "Cliente não possui conta"}

    resource_cartao = await ctx.read_resource(f"cartao://{quote(cpf, safe='')}")
    cartao_existente = extract_resource_data(resource_cartao)
    if cartao_existente and "erro" not in cartao_existente:
        return {"status": "existente", "cartao": cartao_existente}

    numero_cartao = random.randint(100000, 999999)
    cartao = {
        "numero": numero_cartao,
        "tipo": tipo,
        "limite": random.randint(1000, 5000),
    }
    cartoes_mdbank[cpf] = cartao
    save_db()
    return {"status": "criado", "cartao": cartao}


@mcp.tool()
async def gerar_prompt_abertura(nome: str, cpf: str, ctx: Context) -> list:
    """Gera as instruções de abertura de conta com base nos dados informados."""
    prompt = await ctx.get_prompt("abrir_conta_prompt", {"nome": nome, "cpf": cpf})
    return [m.content for m in prompt.messages]
