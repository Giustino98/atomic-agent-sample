import os
from typing import List, Optional
from pydantic import Field
from atomic_agents.agents.base_agent import BaseIOSchema
from serpapi import GoogleSearch


class WebSearchInput(BaseIOSchema):
    """Schema di input per la ricerca sul web."""
    query: str = Field(..., description="La query di ricerca.")
    num_results: int = Field(default=5, description="Il numero di risultati da restituire.")


class WebSearchResult(BaseIOSchema):
    """Schema per un singolo risultato di ricerca."""
    title: str = Field(..., description="Il titolo del risultato.")
    url: str = Field(..., description="L'URL del risultato.")
    snippet: str = Field(..., description="Un breve estratto del risultato.")


class WebSearchOutput(BaseIOSchema):
    """Schema di output per la ricerca sul web."""
    results: List[WebSearchResult] = Field(..., description="I risultati della ricerca.")


class WebSearchTool:
    """Tool per la ricerca sul web utilizzando SerpAPI."""
    input_schema = WebSearchInput
    output_schema = WebSearchOutput

    @staticmethod
    async def execute(input_data: WebSearchInput) -> WebSearchOutput:
        """
        Esegue una ricerca sul web utilizzando SerpAPI con Google Search.
        
        Args:
            input_data: I dati di input per la ricerca.
            
        Returns:
            I risultati della ricerca.
        """
        # Ottieni la chiave API di SerpAPI
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            raise ValueError("La variabile d'ambiente SERPAPI_API_KEY non è impostata.")
        
        # Configura i parametri di ricerca
        params = {
            "engine": "google",
            "q": input_data.query,
            "api_key": api_key,
            "num": input_data.num_results,
            "gl": "it",  # Località: Italia
            "hl": "it"   # Lingua: Italiano
        }
        
        # Esegui la ricerca
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # Estrai i risultati organici
        organic_results = results.get("organic_results", [])
        
        # Converti i risultati nel formato richiesto
        search_results = []
        for result in organic_results:
            search_results.append(
                WebSearchResult(
                    title=result.get("title", ""),
                    url=result.get("link", ""),
                    snippet=result.get("snippet", "")
                )
            )
        
        return WebSearchOutput(results=search_results) 