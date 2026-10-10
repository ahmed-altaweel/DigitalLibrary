from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...schemas.library import ReadingProgressUpdate, ReadingProgressResponse
from ...services import library_service
from ...models.user import User

router = APIRouter()

@router.get("/me/reading-progress", response_model=list[ReadingProgressResponse])
def get_all_progress(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return library_service.get_reading_progress(db, current_user.id)

@router.get("/me/reading-progress/{material_id}", response_model=ReadingProgressResponse)
def get_material_progress(material_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rp = library_service.get_reading_progress(db, current_user.id, material_id)
    if not rp:
        raise HTTPException(status_code=404, detail="Not found")
    return rp

@router.put("/me/reading-progress/{material_id}", response_model=ReadingProgressResponse)
def update_progress(material_id: str, data: ReadingProgressUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return library_service.update_reading_progress(db, current_user.id, material_id, data)
