from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...schemas.library import ReadingListCreate, ReadingListUpdate, ReadingListResponse, ReadingListItemAdd
from ...services import library_service
from ...models.user import User
from ...models.library import ReadingList, ReadingListItem

router = APIRouter()

@router.get("/me/reading-lists", response_model=list[ReadingListResponse])
def get_reading_lists(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(ReadingList).filter(ReadingList.user_id == current_user.id).all()

@router.post("/me/reading-lists", response_model=ReadingListResponse)
def create_reading_list(data: ReadingListCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return library_service.create_reading_list(db, current_user.id, data)

@router.get("/me/reading-lists/{id}")
def get_single_reading_list(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rl = db.query(ReadingList).filter(ReadingList.id == id, ReadingList.user_id == current_user.id).first()
    if not rl:
        raise HTTPException(status_code=404, detail="Not found")
    items = db.query(ReadingListItem).filter(ReadingListItem.reading_list_id == id).all()
    # Serialize manually or rely on ORM lazy load if configured
    return {"list": rl, "items": items}

@router.put("/me/reading-lists/{id}", response_model=ReadingListResponse)
def update_reading_list(id: str, data: ReadingListUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rl = library_service.update_reading_list(db, current_user.id, id, data)
    if not rl:
        raise HTTPException(status_code=404, detail="Not found")
    return rl

@router.delete("/me/reading-lists/{id}")
def delete_reading_list(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    success = library_service.delete_reading_list(db, current_user.id, id)
    if not success:
        raise HTTPException(status_code=404, detail="Not found")
    return {"message": "Deleted"}

@router.post("/me/reading-lists/{id}/items")
def add_item_to_list(id: str, data: ReadingListItemAdd, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = library_service.add_to_reading_list(db, current_user.id, id, data.material_id, data.display_order)
    if not item:
        raise HTTPException(status_code=404, detail="List not found")
    return item

@router.delete("/me/reading-lists/{id}/items/{item_id}")
def remove_item_from_list(id: str, item_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    library_service.remove_from_reading_list(db, current_user.id, id, item_id)
    return {"message": "Removed"}

class ReorderData(BaseModel):
    items: list[dict] # list of {item_id: str, order: int}

@router.put("/me/reading-lists/{id}/reorder")
def reorder_list(id: str, data: ReorderData, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    library_service.reorder_reading_list(db, current_user.id, id, data.items)
    return {"message": "Reordered"}
