from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.dependencies import get_current_admin
from ...schemas.admin import AuditLogResponse, UserAdminResponse, RoleAssignment, PlatformStats
from ...schemas.suggestion import SuggestionResponse, SuggestionReview
from ...services import admin_service, suggestion_service
from ...models.user import User

router = APIRouter()

@router.get("/admin/stats", response_model=PlatformStats)
def get_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    return admin_service.get_platform_stats(db)

@router.get("/admin/users", response_model=list[UserAdminResponse])
def get_users(
    page: int = Query(1, ge=1), 
    size: int = Query(20, ge=1, le=100), 
    search: str = None, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_admin)
):
    users = admin_service.get_users(db, page, size, search)
    res = []
    for u in users:
        res.append({
            "id": u.id,
            "email": u.email,
            "username": u.username,
            "is_active": u.is_active,
            "roles": [r.name for r in u.roles],
            "created_at": u.created_at
        })
    return res

@router.put("/admin/users/{id}/roles", response_model=UserAdminResponse)
def assign_roles(id: str, data: RoleAssignment, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    u = admin_service.update_user_roles(db, id, data.roles)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": u.id,
        "email": u.email,
        "username": u.username,
        "is_active": u.is_active,
        "roles": [r.name for r in u.roles],
        "created_at": u.created_at
    }

@router.put("/admin/users/{id}/deactivate")
def deactivate_user(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    u = admin_service.deactivate_user(db, id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Deactivated"}

@router.get("/admin/suggestions", response_model=list[SuggestionResponse])
def get_pending_suggestions(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    return suggestion_service.get_pending_suggestions(db, page, size)

@router.put("/admin/suggestions/{id}/review", response_model=SuggestionResponse)
def review_suggestion(id: str, data: SuggestionReview, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    s = suggestion_service.review_suggestion(db, current_user.id, id, data.action, data.notes)
    if not s:
        raise HTTPException(status_code=404, detail="Not found")
    return s

@router.get("/admin/audit-logs", response_model=list[AuditLogResponse])
def get_audit_logs(
    page: int = Query(1, ge=1), 
    size: int = Query(20, ge=1, le=100), 
    action: str = None,
    user_id: str = None,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_admin)
):
    filters = {}
    if action: filters["action"] = action
    if user_id: filters["user_id"] = user_id
    return admin_service.get_audit_logs(db, page, size, filters)
