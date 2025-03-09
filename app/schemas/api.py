from pydantic import BaseModel


class QuestionRequest(BaseModel):
    """Schema per la richiesta di una domanda."""
    question: str


class AnswerResponse(BaseModel):
    """Schema per la risposta a una domanda."""
    answer: str 