from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from anthropic import Anthropic
from dotenv import load_dotenv
import base64
import os

load_dotenv()

app = FastAPI()
client = Anthropic()

# CORS — permite que o frontend (GitHub Pages) chame o backend (Render)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

SYSTEM_PROMPT = """Você é um assistente de descrição visual para pessoas com deficiência visual.
O usuário vai fazer um pedido em linguagem natural sobre o que a câmera está mostrando.

Regras absolutas:
- Responda APENAS em português do Brasil
- Seja claro, direto e natural — como alguém descrevendo verbalmente para um amigo
- SEM markdown, asteriscos, listas, emojis ou qualquer formatação
- Máximo 4 frases por resposta
- Adapte sua descrição ao pedido do usuário:
  * "o que é isso" → descreva o objeto principal: tipo, cor, forma, tamanho aproximado
  * "o que tem no ambiente" ou "onde estou" → descreva o espaço: o que domina a cena, objetos presentes, iluminação
  * "que roupa é essa" → descreva: tipo de peça, cor, estampa, material aparente
  * "leia isso" ou "o que está escrito" → leia o texto visível, palavra por palavra se necessário
  * "que cor é essa" → nomeie as cores com precisão
  * "o que tem dentro" → liste o que é visível
  * Qualquer outro pedido → use bom senso para descrever o que for mais relevante
- Se a imagem estiver escura, borrada ou sem objeto claro, informe de forma gentil
- Nunca diga "não posso ver" — descreva o que está na imagem, mesmo que parcialmente"""


# — MODELO —

class DescricaoRequest(BaseModel):
    pedido: str
    imagem_base64: str  # JPEG em base64


# — ROTA —

@app.post("/descrever")
async def descrever(req: DescricaoRequest):
    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": req.imagem_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": req.pedido
                    }
                ]
            }]
        )
        return {"descricao": response.content[0].text.strip()}

    except Exception as e:
        print(f"Erro ao chamar a API: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar a imagem.")


# — FRONTEND —
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
