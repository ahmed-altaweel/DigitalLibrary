from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...schemas.suggestion import SuggestionCreate, SuggestionResponse
from ...services import suggestion_service
from ...models.user import User

router = APIRouter()

@router.post("/materials/{material_id}/suggestions", response_model=SuggestionResponse)
def submit_suggestion(material_id: str, data: SuggestionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return suggestion_service.create_suggestion(db, current_user.id, material_id, data)

@router.get("/me/suggestions", response_model=list[SuggestionResponse])
def get_my_suggestions(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return suggestion_service.get_user_suggestions(db, current_user.id, page, size)

@router.put("/me/suggestions/{id}/withdraw", response_model=SuggestionResponse)
def withdraw_suggestion(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    s = suggestion_service.withdraw_suggestion(db, current_user.id, id)
    if not s:
        raise HTTPException(status_code=404, detail="Not found")
    return s
