from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from agente import criar_grafo
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API")

app = FastAPI(title="API Validador de Pricing")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PricingInput(BaseModel):
    cac: float
    preco: float
    rpc: float

@app.post("/analisar")
async def analisar_pricing(dados: PricingInput):
    logger.info(f"Recebendo requisição: {dados}")
    try:

        grafo = criar_grafo()
        

        inputs = {
            "custo_unitario_cac": dados.cac,
            "preco_segmento_minimo": dados.preco,
            "renda_per_capita_min": dados.rpc,
            "violacoes": [],
            "alertas": [],
            "relatorio": "",
            "feedback_llm": ""
        }
        
        thread = {"configurable": {"thread_id": "api_request"}}
        

        final_state = grafo.invoke(inputs, config=thread)
        
        return {
            "relatorio": final_state["relatorio"],
            "feedback_llm": final_state["feedback_llm"],
            "violacoes": final_state["violacoes"],
            "alertas": final_state["alertas"]
        }
    except Exception as e:
        logger.error(f"Erro interno na API: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Servidor Backend rodando!")
    print("📄 Documentação da API: http://localhost:8000/docs")
    print("📡 Endpoint de Análise: http://localhost:8000/analisar\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
