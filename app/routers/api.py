from fastapi import APIRouter, Depends, HTTPException
from app.schemas.api import QuestionRequest, AnswerResponse
from app.agents.info_agent import InfoAgent

router = APIRouter()

# Dependency per ottenere l'agente
def get_info_agent():
    return InfoAgent()

@router.post("/ask", response_model=AnswerResponse)
async def ask_question(
    request: QuestionRequest,
    agent: InfoAgent = Depends(get_info_agent)
):
    """
    Endpoint per fare una domanda all'agente e ricevere una risposta.
    """
    try:
        answer = await agent.ask(request.question)
        return AnswerResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore durante l'elaborazione della domanda: {str(e)}") 