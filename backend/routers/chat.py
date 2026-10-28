
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.rag_chain import ask_question

router = APIRouter(
    prefix="/api",
    tags=["Chat"],
)


class ChatRequest(BaseModel):
    question: str


@router.post("/chat")
def chat(request: ChatRequest):
    try:
        return ask_question(request.question)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your question.",
        )
