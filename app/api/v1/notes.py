from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...schemas.library import UserNoteCreate, UserNoteUpdate, UserNoteResponse
from ...services import library_service
from ...models.user import User
from pydantic import BaseModel

router = APIRouter()

class CreateNoteReq(UserNoteCreate):
    material_id: str

@router.get("/me/notes", response_model=list[UserNoteResponse])
def get_all_notes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return library_service.get_notes(db, current_user.id)

@router.get("/me/notes/material/{material_id}", response_model=list[UserNoteResponse])
def get_material_notes(material_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return library_service.get_notes(db, current_user.id, material_id)

@router.post("/me/notes", response_model=UserNoteResponse)
def create_note(data: CreateNoteReq, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return library_service.create_note(db, current_user.id, data.material_id, data)

@router.put("/me/notes/{id}", response_model=UserNoteResponse)
def update_note(id: str, data: UserNoteUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    n = library_service.update_note(db, current_user.id, id, data)
    if not n:
        raise HTTPException(status_code=404, detail="Not found")
    return n

@router.delete("/me/notes/{id}")
def delete_note(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    success = library_service.delete_note(db, current_user.id, id)
    if not success:
        raise HTTPException(status_code=404, detail="Not found")
    return {"message": "Deleted"}
