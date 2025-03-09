# Atomic Agent API

Questa è un'applicazione FastAPI che utilizza il framework Atomic Agents per creare agenti che recuperano informazioni da tool esterni e rispondono alle domande degli utenti.

## Installazione

1. Clona questo repository
2. Installa le dipendenze:
   ```
   pip install -r requirements.txt
   ```
3. Crea un file `.env` nella directory principale e aggiungi le seguenti variabili d'ambiente:
   ```
   # Configurazione OpenAI (opzionale se usi Ollama)
   OPENAI_API_KEY=your_openai_api_key_here
   MODEL_NAME=gpt-4-turbo
   
   # Configurazione SerpAPI (richiesta)
   SERPAPI_API_KEY=your_serpapi_api_key_here
   
   # Configurazione Ollama (per utilizzare LLM gratuiti localmente)
   USE_OLLAMA=true
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3
   ```

### Ottenere le chiavi API

- **OpenAI API Key**: Registrati su [OpenAI](https://platform.openai.com/) e ottieni una chiave API (opzionale se usi Ollama).
- **SerpAPI Key**: Registrati su [SerpAPI](https://serpapi.com/) e ottieni una chiave API gratuita. SerpAPI offre un piano gratuito con 100 ricerche al mese.

### Configurazione di Ollama (alternativa gratuita a OpenAI)

Per utilizzare modelli LLM gratuiti localmente:

1. Installa Ollama seguendo le istruzioni su [Ollama.ai](https://ollama.ai/)
2. Avvia il server Ollama
3. Scarica un modello (ad esempio Llama 3):
   ```
   ollama pull llama3
   ```
4. Imposta `USE_OLLAMA=true` nel file `.env`

## Avvio dell'applicazione

Per avviare l'applicazione, esegui:

```
uvicorn app.main:app --reload
```

L'applicazione sarà disponibile all'indirizzo `http://localhost:8000`.

## API

### Endpoint: `/api/ask`

Questo endpoint accetta una domanda dall'utente e restituisce una risposta generata utilizzando il framework Atomic Agents.

**Metodo**: POST

**Payload**:
```json
{
  "question": "Qual è la capitale dell'Italia?"
}
```

**Risposta**:
```json
{
  "answer": "La capitale dell'Italia è Roma."
}
```

## Struttura del progetto

- `app/`: Directory principale dell'applicazione
  - `main.py`: File principale dell'applicazione FastAPI
  - `routers/`: Directory contenente i router FastAPI
    - `api.py`: Router per l'API
  - `agents/`: Directory contenente gli agenti Atomic Agents
    - `info_agent.py`: Agente per recuperare informazioni
  - `tools/`: Directory contenente i tool utilizzati dagli agenti
    - `web_search.py`: Tool per la ricerca sul web utilizzando SerpAPI
  - `schemas/`: Directory contenente gli schemi Pydantic
    - `api.py`: Schemi per l'API

## Altre alternative gratuite

Oltre a Ollama, puoi considerare:

1. **Hugging Face**: Offre modelli gratuiti tramite la loro API Inference
2. **Groq**: Offre un piano gratuito con un numero limitato di richieste
3. **Anthropic Claude**: Offre un piano gratuito limitato
4. **Mistral AI**: Offre alcuni modelli gratuiti

Per utilizzare questi provider, dovrai modificare il codice in `info_agent.py` in modo simile a quanto fatto per Ollama.