from sqlalchemy.orm import Session
from datetime import datetime, timezone
from ..models.suggestion import CatalogSuggestion

def create_suggestion(db: Session, user_id: str, material_id: str, data):
    s = CatalogSuggestion(
        material_id=material_id,
        submitted_by=user_id,
        suggestion_type=data.suggestion_type,
        field_name=data.field_name,
        current_value=data.current_value,
        proposed_value=data.proposed_value,
        reason=data.reason
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s

def withdraw_suggestion(db: Session, user_id: str, suggestion_id: str):
    s = db.query(CatalogSuggestion).filter(CatalogSuggestion.id == suggestion_id, CatalogSuggestion.submitted_by == user_id).first()
    if s:
        s.status = 'withdrawn'
        db.commit()
    return s

def review_suggestion(db: Session, reviewer_id: str, suggestion_id: str, action: str, notes: str):
    s = db.query(CatalogSuggestion).filter(CatalogSuggestion.id == suggestion_id).first()
    if s:
        s.status = action
        s.reviewed_by = reviewer_id
        s.review_notes = notes
        s.reviewed_at = datetime.now(timezone.utc)
        db.commit()
    return s

def get_user_suggestions(db: Session, user_id: str, page: int, size: int):
    return db.query(CatalogSuggestion).filter(CatalogSuggestion.submitted_by == user_id).offset((page-1)*size).limit(size).all()

def get_pending_suggestions(db: Session, page: int, size: int):
    return db.query(CatalogSuggestion).filter(CatalogSuggestion.status == 'pending').offset((page-1)*size).limit(size).all()
