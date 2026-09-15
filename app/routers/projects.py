from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(prefix="/projects", tags=["projects"])


def get_owned_project(project_id: int, db: Session, user: models.User) -> models.Project:
    """Shared helper: fetch a project and enforce that the current user owns it.
    Reused by chat.py and files.py to keep authorization logic in one place."""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your project")
    return project


@router.post("", response_model=schemas.ProjectOut, status_code=201)
def create_project(
    payload: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    project = models.Project(user_id=user.id, **payload.dict())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=List[schemas.ProjectOut])
def list_projects(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.Project).filter(models.Project.user_id == user.id).all()


@router.get("/{project_id}", response_model=schemas.ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return get_owned_project(project_id, db, user)


@router.put("/{project_id}", response_model=schemas.ProjectOut)
def update_project(
    project_id: int,
    payload: schemas.ProjectUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    project = get_owned_project(project_id, db, user)
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    project = get_owned_project(project_id, db, user)
    db.delete(project)
    db.commit()
    return None


@router.get("/{project_id}/messages", response_model=List[schemas.MessageOut])
def get_messages(project_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    project = get_owned_project(project_id, db, user)
    return (
        db.query(models.Message)
        .filter(models.Message.project_id == project.id)
        .order_by(models.Message.created_at)
        .all()
    )
