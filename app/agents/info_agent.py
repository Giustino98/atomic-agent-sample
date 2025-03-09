import os
from typing import List
import instructor
from openai import OpenAI
from pydantic import Field
from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from app.tools.web_search import WebSearchTool, WebSearchInput
# Importiamo le librerie necessarie per Ollama
import httpx
from instructor.patch import wrap_chatcompletion


class InfoAgentInput(BaseIOSchema):
    """Schema di input per l'agente informativo."""
    question: str = Field(..., description="La domanda dell'utente.")


class InfoAgentOutput(BaseIOSchema):
    """Schema di output per l'agente informativo."""
    answer: str = Field(..., description="La risposta alla domanda dell'utente.")


# Classe per il client Ollama
class OllamaClient:
    def __init__(self, base_url, model):
        self.base_url = base_url
        self.model = model
        self.client = httpx.Client(timeout=60.0)
    
    def chat_completions_create(self, messages, **kwargs):
        response = self.client.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                **kwargs
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Adattiamo la risposta di Ollama al formato di OpenAI
        return type('OllamaResponse', (), {
            'choices': [
                type('Choice', (), {
                    'message': type('Message', (), {
                        'content': data['message']['content'],
                        'role': data['message']['role']
                    }),
                    'index': 0
                })
            ],
            'model': self.model
        })


class InfoAgent:
    """
    Agente che recupera informazioni da tool esterni e risponde alle domande degli utenti.
    """
    def __init__(self):
        # Determiniamo se usare Ollama o OpenAI
        use_ollama = os.getenv("USE_OLLAMA", "false").lower() == "true"
        
        if use_ollama:
            # Configurazione per Ollama
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            model_name = os.getenv("OLLAMA_MODEL", "llama3")
            
            # Creiamo il client Ollama
            ollama_client = OllamaClient(base_url, model_name)
            
            # Utilizziamo instructor per wrappare il client Ollama
            self.client = wrap_chatcompletion(ollama_client)
        else:
            # Configurazione per OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("La variabile d'ambiente OPENAI_API_KEY non è impostata e USE_OLLAMA è false.")
            
            model_name = os.getenv("MODEL_NAME", "gpt-4-turbo")
            
            # Creazione del client OpenAI con instructor
            self.client = instructor.from_openai(OpenAI(api_key=api_key))
        
        # Configurazione dell'agente
        self.config = BaseAgentConfig(
            system_prompt="""
            Sei un assistente AI esperto nel recuperare informazioni e rispondere alle domande degli utenti.
            Utilizza i tool a tua disposizione per trovare le informazioni più pertinenti e fornire risposte accurate.
            Sii conciso ma completo nelle tue risposte.
            """,
            input_schema=InfoAgentInput,
            output_schema=InfoAgentOutput,
            model=model_name,
            client=self.client  # Passiamo il client configurato
        )
        
        # Creazione dell'agente
        self.agent = BaseAgent(self.config)
        
        # Registrazione del tool di ricerca web
        self.web_search_tool = WebSearchTool()
        self.agent.register_tool("web_search", self.web_search_tool)
    
    async def ask(self, question: str) -> str:
        """
        Processa una domanda e restituisce una risposta.
        
        Args:
            question: La domanda dell'utente.
            
        Returns:
            La risposta alla domanda.
        """
        # Creazione dell'input per l'agente
        agent_input = InfoAgentInput(question=question)
        
        # Esecuzione dell'agente
        response = await self.agent.arun(agent_input)
        
        return response.answer 