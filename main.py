from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re
import time
from collections import defaultdict

app = FastAPI(title="Chatbot com Guardrails – Responsible AI")

# =========================
# 7️⃣ ANÁLISE E MÉTRICAS
# =========================

metricas = defaultdict(int)
logs = []

def coletar_evento(evento, camada, detalhe=""):
    metricas[evento] += 1
    logs.append({
        "evento": evento,
        "camada": camada,
        "detalhe": detalhe,
        "timestamp": time.time()
    })

# =========================
# MODELO DE ENTRADA
# =========================

class Mensagem(BaseModel):
    mensagem: str

# =========================
# 1️⃣ INPUT GUARDRAIL
# =========================

PALAVRAS_PROIBIDAS = [
    "ignore as regras",
    "ignore todas as instruções",
    "revele o prompt",
    "você agora é"
]

def input_guardrail(texto: str):
    for p in PALAVRAS_PROIBIDAS:
        if p in texto.lower():
            coletar_evento("prompt_injection", "input_guardrail", p)
            raise HTTPException(
                status_code=403,
                detail="Solicitação bloqueada por segurança."
            )

# =========================
# 2️⃣ ANALISADOR DE RISCO
# =========================

def analisador_risco(texto: str):
    riscos = ["fraude", "burlar", "enganar", "crime"]
    for r in riscos:
        if r in texto.lower():
            coletar_evento("abuse_misuse", "analise_risco", r)
            return "alto"
    return "baixo"

# =========================
# 3️⃣ POLICY ENGINE
# =========================

def policy_engine(nivel_risco: str):
    if nivel_risco == "alto":
        coletar_evento("bloqueio_policy", "policy_engine")
        raise HTTPException(
            status_code=403,
            detail="Conteúdo não permitido pela política."
        )

# =========================
# 4️⃣ ORQUESTRADOR DE PROMPT
# =========================

def orquestrador_prompt(texto: str):
    return f"""
Você é um assistente financeiro do Itaú.
Responda de forma segura e objetiva.

Pergunta do cliente:
{texto}
"""

# =========================
# 5️⃣ LLM (SIMULADO)
# =========================

def llm_simulado(prompt: str):
    # Aqui entraria o GPT / modelo real
    return "Esta é uma resposta simulada do chatbot."

# =========================
# 6️⃣ OUTPUT GUARDRAIL
# =========================

def output_guardrail(resposta: str):
    if re.search(r"\b\d{11}\b", resposta):
        coletar_evento("data_leakage", "output_guardrail")
        raise HTTPException(
            status_code=500,
            detail="Resposta bloqueada por vazamento de dados."
        )
    return resposta

# =========================
# ENDPOINT PRINCIPAL
# =========================

@app.post("/chat")
def chat(m: Mensagem):
    input_guardrail(m.mensagem)

    risco = analisador_risco(m.mensagem)

    policy_engine(risco)

    prompt = orquestrador_prompt(m.mensagem)

    resposta = llm_simulado(prompt)

    resposta_final = output_guardrail(resposta)

    coletar_evento("resposta_ok", "sistema")

    return {"resposta": resposta_final}

# =========================
# ENDPOINTS DE MÉTRICAS
# =========================

@app.get("/metricas")
def ver_metricas():
    return dict(metricas)

@app.get("/logs")
def ver_logs():
    return logs

@app.get("/status")
def status():
    return {"status": "Chatbot com guardrails ativo"}
