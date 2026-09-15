from fastapi import APIRouter, Depends, HTTPException
from openai import AsyncOpenAI, OpenAIError
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.routers.projects import get_owned_project

router = APIRouter(prefix="/projects", tags=["chat"])

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


@router.post("/{project_id}/chat", response_model=schemas.ChatResponse)
async def chat(
    project_id: int,
    payload: schemas.ChatRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    # Make sure the project exists and belongs to the current user.
    project = get_owned_project(project_id, db, user)

    # Only active projects can receive chat messages.
    if project.status != "active":
        raise HTTPException(
            status_code=400,
            detail="Project is inactive",
        )

    # Load the existing conversation history from the database.
    history = (
        db.query(models.Message)
        .filter(models.Message.project_id == project.id)
        .order_by(
            models.Message.created_at,
            models.Message.id,
        )
        .all()
    )

    # Convert stored messages into OpenAI input format.
    input_items = [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in history
    ]

    # Add the current user message to the request,
    # but don't save it to the database yet.
    input_items.append(
        {
            "role": "user",
            "content": payload.message,
        }
    )

    # Call the LLM before modifying the database.
    try:
        response = await client.responses.create(
            model=settings.OPENAI_MODEL,
            instructions=project.system_prompt,
            input=input_items,
        )

        reply_text = response.output_text

    except OpenAIError:
        # Since neither message has been committed yet,
        # a provider failure leaves the database unchanged.
        raise HTTPException(
            status_code=502,
            detail="LLM provider error",
        )

    # Only save the conversation after the LLM succeeds.
    user_msg = models.Message(
        project_id=project.id,
        role="user",
        content=payload.message,
    )

    assistant_msg = models.Message(
        project_id=project.id,
        role="assistant",
        content=reply_text,
    )

    db.add_all([user_msg, assistant_msg])
    db.commit()
    db.refresh(assistant_msg)

    return schemas.ChatResponse(
        reply=reply_text,
        message_id=assistant_msg.id,
    )