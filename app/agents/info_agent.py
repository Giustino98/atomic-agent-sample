import os
from typing import List
import instructor
from openai import OpenAI
from pydantic import Field
import logging
import json
import time
from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator, SystemPromptContextProviderBase
from app.tools.web_search import WebSearchTool, WebSearchInput
import httpx


# Configurazione del logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("info_agent_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("InfoAgent")


class InfoAgentInput(BaseIOSchema):
    """Schema di input per l'agente informativo."""
    question: str = Field(..., description="La domanda dell'utente.")


class InfoAgentOutput(BaseIOSchema):
    """Schema di output per l'agente informativo."""
    answer: str = Field(..., description="La risposta alla domanda dell'utente.")


class OllamaClient(OpenAI):
    def __init__(self, base_url, model):
        super().__init__(api_key="ollama")
        self.base_url = base_url
        self.model = model
        self.http_client = httpx.Client(timeout=60.0)
        logger.debug(f"OllamaClient inizializzato con base_url={base_url}, model={model}")

    def chat_completions_create(self, model=None, messages=None, **kwargs):
        model_to_use = model or self.model
        logger.debug(f"Richiesta a Ollama: model={model_to_use}, messages={json.dumps(messages, ensure_ascii=False)[:500]}...")
        
        start_time = time.time()
        try:
            response = self.http_client.post(
                f"{self.base_url}/api/chat",
                json={"model": model_to_use, "messages": messages, "stream": False, **kwargs}
            )
            response.raise_for_status()
            data = response.json()
            
            elapsed_time = time.time() - start_time
            logger.debug(f"Risposta ricevuta da Ollama in {elapsed_time:.2f} secondi")
            logger.debug(f"Contenuto risposta: {data['message']['content'][:200]}...")
            
            return type('OllamaResponse', (), {
                'choices': [type('Choice', (), {'message': type('Message', (), {'content': data['message']['content'], 'role': data['message']['role']}), 'index': 0})],
                'model': model_to_use
            })
        except Exception as e:
            logger.error(f"Errore nella richiesta a Ollama: {str(e)}")
            raise


class WebSearchContextProvider(SystemPromptContextProviderBase):
    """
    Context provider per i risultati di ricerca web.
    Fornisce i risultati di ricerca come contesto per l'agente.
    """
    def __init__(self, web_search_tool: WebSearchTool, question: str, num_results: int = 5):
        super().__init__(title="Risultati di Ricerca Web")
        self.web_search_tool = web_search_tool
        self.question = question
        self.num_results = num_results
        self._search_results = []
        logger.debug(f"WebSearchContextProvider inizializzato con question={question}, num_results={num_results}")
        # Inizializziamo i risultati come lista vuota
        # La ricerca effettiva verrà eseguita quando necessario

    def get_info(self) -> str:
        """
        Ottiene le informazioni di contesto dai risultati di ricerca.
        
        Returns:
            Le informazioni di contesto formattate.
        """
        if not self._search_results:
            logger.warning("Nessun risultato di ricerca trovato")
            return "Nessun risultato di ricerca trovato."
        
        formatted_results = "\n".join([f"{i+1}. {res.title}\n{res.url}\n{res.snippet}" for i, res in enumerate(self._search_results)])
        logger.debug(f"Formattati {len(self._search_results)} risultati di ricerca")
        return formatted_results

    def set_search_results(self, results: List[dict]):
        """
        Imposta i risultati di ricerca.
        
        Args:
            results: I risultati della ricerca.
        """
        logger.debug(f"Impostati {len(results)} risultati di ricerca")
        self._search_results = results


class InfoAgent:
    """
    Agente che recupera informazioni da tool esterni e risponde alle domande degli utenti.
    Utilizza un context provider per integrare i risultati di ricerca web nel contesto dell'agente.
    """
    def __init__(self):
        logger.info("Inizializzazione InfoAgent")
        
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/api")
        model_name = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
        logger.info(f"Configurazione: base_url={base_url}, model_name={model_name}")

        # Verifica la connessione a Ollama
        self.test_ollama_connection(base_url, model_name)

        self.client = instructor.from_openai(OllamaClient(base_url=base_url, model=model_name))
        logger.debug("Client instructor inizializzato")

        self.web_search_tool = WebSearchTool()
        logger.debug("WebSearchTool inizializzato")

        self.system_prompt_generator = SystemPromptGenerator(
            background=[
                "Sei un assistente AI esperto nel recuperare informazioni e rispondere alle domande degli utenti.",
                "Utilizzi i risultati di ricerca web per fornire risposte accurate e aggiornate.",
                "Sei in grado di analizzare e sintetizzare informazioni da diverse fonti."
            ],
            steps=[
                "Analizza attentamente la domanda dell'utente.",
                "Esamina i risultati di ricerca forniti nel contesto.",
                "Sintetizza le informazioni rilevanti dai risultati di ricerca.",
                "Formula una risposta completa e accurata basata sulle informazioni trovate."
            ],
            output_instructions=[
                "Fornisci risposte concise ma complete.",
                "Cita le fonti quando appropriato.",
                "Se non trovi informazioni sufficienti nei risultati di ricerca, indicalo chiaramente.",
                "Evita di inventare informazioni non presenti nei risultati di ricerca."
            ]
        )
        logger.debug("SystemPromptGenerator inizializzato")

        self.config = BaseAgentConfig(
            client=self.client,
            model=model_name,
            system_prompt_generator=self.system_prompt_generator,
            input_schema=InfoAgentInput,
            output_schema=InfoAgentOutput
        )
        logger.debug("BaseAgentConfig inizializzato")

        self.agent = BaseAgent(self.config)
        logger.debug("BaseAgent inizializzato")
        logger.info("InfoAgent completamente inizializzato")

    async def ask(self, question: str) -> str:
        """
        Processa una domanda e restituisce una risposta.
        
        Args:
            question: La domanda dell'utente.
            
        Returns:
            La risposta alla domanda.
        """
        logger.info(f"Elaborazione domanda: {question}")
        
        agent_input = InfoAgentInput(question=question)
        logger.debug(f"Creato input per l'agente: {agent_input}")

        # Esegui la ricerca web e imposta i risultati nel context provider
        logger.info("Avvio ricerca web")
        web_search_provider = WebSearchContextProvider(self.web_search_tool, question)
        
        try:
            start_time = time.time()
            search_results = await self.web_search_tool.execute(WebSearchInput(query=question, num_results=5))
            elapsed_time = time.time() - start_time
            logger.info(f"Ricerca web completata in {elapsed_time:.2f} secondi, trovati {len(search_results.results)} risultati")
            
            web_search_provider.set_search_results(search_results.results)
            logger.debug("Risultati di ricerca impostati nel context provider")
        except Exception as e:
            logger.error(f"Errore durante la ricerca web: {str(e)}")
            logger.warning("Continuo senza risultati di ricerca")
            web_search_provider.set_search_results([])

        # Registra il context provider
        self.agent.register_context_provider("web_search_results", web_search_provider)

        # Esegui l'agente direttamente
        logger.info("Avvio esecuzione agente")
        try:
            response = self.agent.run(agent_input)
            logger.debug(f"Risposta dell'agente: {response.answer[:200]}...")
            return response.answer
        except Exception as e:
            logger.error(f"Errore durante l'esecuzione dell'agente: {str(e)}")
            