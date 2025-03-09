import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routers import api

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Verifica che le chiavi API necessarie siano impostate
use_ollama = os.getenv("USE_OLLAMA", "false").lower() == "true"

if not use_ollama and not os.getenv("OPENAI_API_KEY"):
    raise ValueError("La variabile d'ambiente OPENAI_API_KEY non è impostata e USE_OLLAMA è false. Assicurati di configurare una delle due opzioni nel file .env.")

if not os.getenv("SERPAPI_API_KEY"):
    raise ValueError("La variabile d'ambiente SERPAPI_API_KEY non è impostata. Assicurati di averla configurata nel file .env.")

# Crea l'applicazione FastAPI
app = FastAPI(
    title="Atomic Agent API",
    description="API per interagire con agenti che utilizzano il framework Atomic Agents",
    version="0.1.0"
)

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, specifica i domini consentiti
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Includi i router
app.include_router(api.router, prefix="/api", tags=["api"])

# Endpoint di root
@app.get("/")
async def root():
    return {
        "message": "Benvenuto nell'API Atomic Agent",
        "docs": "/docs",
        "endpoints": {
            "ask": "/api/ask"
        }
    }

# Se questo file viene eseguito direttamente
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 