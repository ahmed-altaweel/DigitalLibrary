from sqlalchemy.orm import Session

from ..models.material import Material
from ..models.suggestion import AuditLog
from ..models.user import Role, User
from .auth_service import revoke_all_refresh_tokens


def get_users(db: Session, page: int, size: int, search: str = None):
    q = db.query(User)
    if search:
        q = q.filter(User.email.ilike(f"%{search}%"))
    return q.order_by(User.created_at.desc(), User.id).offset((page-1)*size).limit(size).all()

def update_user_roles(db: Session, user_id: str, roles: list[str]):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    db_roles = db.query(Role).filter(Role.name.in_(roles)).all()
    user.roles = db_roles
    db.commit()
    db.refresh(user)
    return user

def deactivate_user(db: Session, user_id: str):
    u = db.query(User).filter(User.id == user_id).first()
    if u:
        u.is_active = False
        revoke_all_refresh_tokens(db, u.id, commit=False)  # also kill every active session
        db.commit()
        return u
    return None

def activate_user(db: Session, user_id: str):
    u = db.query(User).filter(User.id == user_id).first()
    if u:
        u.is_active = True
        db.commit()
        return u
    return None

def get_audit_logs(db: Session, page: int, size: int, filters: dict):
    q = db.query(AuditLog)
    if filters.get("action"):
        q = q.filter(AuditLog.action == filters["action"])
    if filters.get("user_id"):
        q = q.filter(AuditLog.user_id == filters["user_id"])
    return q.order_by(AuditLog.created_at.desc(), AuditLog.id).offset((page-1)*size).limit(size).all()

def log_action(db: Session, user_id: str, action: str, entity_type: str, entity_id: str, details: dict, request=None):
    ip_address = request.client.host if request and request.client else None
    user_agent = request.headers.get("user-agent") if request else None
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(log)
    db.commit()

def get_platform_stats(db: Session):
    return {
        "total_users": db.query(User).count(),
        "total_materials": db.query(Material).count(),
        "total_downloads": 0,
        "active_users_last_30_days": 0
    }