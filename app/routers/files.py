from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from openai import AsyncOpenAI, OpenAIError
from sqlalchemy.orm import Session

from app import models
from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.routers.projects import get_owned_project

router = APIRouter(prefix="/projects", tags=["files"])

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


@router.post("/{project_id}/files")
async def upload_file(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    project = get_owned_project(project_id, db, user)
    contents = await file.read()

    try:
        uploaded = await client.files.create(file=(file.filename, contents), purpose="assistants")
    except OpenAIError as e:
        raise HTTPException(status_code=502, detail=f"File upload failed: {e}")

    record = models.ProjectFile(project_id=project.id, openai_file_id=uploaded.id, filename=file.filename)
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"id": record.id, "filename": record.filename, "openai_file_id": record.openai_file_id}


@router.get("/{project_id}/files")
def list_files(project_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    project = get_owned_project(project_id, db, user)
    return [
        {"id": f.id, "filename": f.filename, "openai_file_id": f.openai_file_id}
        for f in project.files
    ]
