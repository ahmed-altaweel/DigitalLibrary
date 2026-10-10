from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...schemas.library import BookmarkCreate, BookmarkUpdate, BookmarkResponse
from ...services import library_service
from ...models.user import User
from pydantic import BaseModel

router = APIRouter()

class CreateBookmarkReq(BookmarkCreate):
    material_id: str

@router.get("/me/bookmarks", response_model=list[BookmarkResponse])
def get_all_bookmarks(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return library_service.get_bookmarks(db, current_user.id)

@router.get("/me/bookmarks/material/{material_id}", response_model=list[BookmarkResponse])
def get_material_bookmarks(material_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return library_service.get_bookmarks(db, current_user.id, material_id)

@router.post("/me/bookmarks", response_model=BookmarkResponse)
def create_bookmark(data: CreateBookmarkReq, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return library_service.create_bookmark(db, current_user.id, data.material_id, data)

@router.put("/me/bookmarks/{id}", response_model=BookmarkResponse)
def update_bookmark(id: str, data: BookmarkUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    b = library_service.update_bookmark(db, current_user.id, id, data)
    if not b:
        raise HTTPException(status_code=404, detail="Not found")
    return b

@router.delete("/me/bookmarks/{id}")
def delete_bookmark(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    success = library_service.delete_bookmark(db, current_user.id, id)
    if not success:
        raise HTTPException(status_code=404, detail="Not found")
    return {"message": "Deleted"}
