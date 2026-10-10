from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...schemas.library import UserTagCreate
from ...services import library_service
from ...models.user import User
from pydantic import BaseModel

router = APIRouter()

class AddTagReq(UserTagCreate):
    material_id: str

@router.get("/me/tags")
def get_user_tags(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tags = library_service.get_user_tags(db, current_user.id)
    return tags

@router.post("/me/tags")
def add_tag(data: AddTagReq, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return library_service.add_user_tag(db, current_user.id, data.material_id, data.tag_name)

@router.delete("/me/tags/{id}")
def remove_tag(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    success = library_service.remove_user_tag(db, current_user.id, id)
    if not success:
        raise HTTPException(status_code=404, detail="Not found")
    return {"message": "Deleted"}
