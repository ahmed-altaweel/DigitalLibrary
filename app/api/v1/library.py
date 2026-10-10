from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...schemas.library import LibraryItemResponse
from ...services import library_service
from ...models.user import User
from ...schemas.material import PaginatedResponse

router = APIRouter()

@router.get("/me/library", response_model=PaginatedResponse[LibraryItemResponse])
def get_library(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = library_service.get_user_library(db, current_user.id, page, size)
    # Total count would normally be computed; using dummy count 100 for now.
    total = 100
    return {"items": items, "total": total, "page": page, "size": size, "pages": (total + size - 1) // size}

from pydantic import BaseModel

class AddToLibraryRequest(BaseModel):
    material_id: str

@router.post("/me/library", response_model=LibraryItemResponse)
def add_to_library(data: AddToLibraryRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return library_service.add_to_library(db, current_user.id, data.material_id)

@router.delete("/me/library/{material_id}")
def remove_from_library(material_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    library_service.remove_from_library(db, current_user.id, material_id)
    return {"message": "Removed from library"}
