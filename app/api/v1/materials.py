from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.dependencies import get_current_admin, get_current_editor, get_optional_user, user_has_role
from ...models.user import User
from ...schemas.material import (
    MaterialCreate,
    MaterialListResponse,
    MaterialResponse,
    MaterialUpdate,
    PaginatedResponse,
)
from ...services import material_service

router = APIRouter()


def _is_staff(user: User | None) -> bool:
    return user_has_role(user, "admin", "editor")


@router.get("/", response_model=PaginatedResponse[MaterialListResponse])
def get_materials(
    q: str | None = Query(None, max_length=200),
    content_type: str | None = None,
    category_id: str | None = None,
    tag_id: str | None = None,
    author_id: str | None = None,
    status: Literal["draft", "published", "archived"] = "published",
    sort: Literal["created_at", "title", "published_at", "view_count", "download_count"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    # Only staff may list unpublished material; everyone else always sees "published".
    if status != "published" and not _is_staff(current_user):
        status = "published"
    filters = {
        "status": status,
        "content_type": content_type,
        "category_id": category_id,
        "tag_id": tag_id,
        "author_id": author_id,
    }
    items, total = material_service.search_materials(db, q, filters, page, size, sort, order == "desc")
    return {"items": items, "total": total, "page": page, "size": size, "pages": (total + size - 1) // size}


@router.get("/{id_or_slug}", response_model=MaterialResponse)
def get_material(id_or_slug: str, db: Session = Depends(get_db), current_user: User | None = Depends(get_optional_user)):
    material = material_service.get_material(db, id_or_slug, current_user)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    if material.publication_status != "published" and not _is_staff(current_user):
        raise HTTPException(status_code=404, detail="Material not found")
    return material


@router.post("/", response_model=MaterialResponse)
def create_material(data: MaterialCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_editor)):
    return material_service.create_material(db, data, current_user.id)


def _or_404(material):
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material


@router.put("/{id}", response_model=MaterialResponse)
def update_material(id: str, data: MaterialUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_editor)):
    return _or_404(material_service.update_material(db, id, data, current_user.id))


@router.delete("/{id}")
def delete_material(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    if not material_service.delete_material(db, id):
        raise HTTPException(status_code=404, detail="Material not found")
    return {"message": "Material deleted"}


@router.post("/{id}/publish", response_model=MaterialResponse)
def publish_material(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_editor)):
    return _or_404(material_service.publish_material(db, id))


@router.post("/{id}/unpublish", response_model=MaterialResponse)
def unpublish_material(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_editor)):
    return _or_404(material_service.unpublish_material(db, id))


@router.post("/{id}/archive", response_model=MaterialResponse)
def archive_material(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_editor)):
    return _or_404(material_service.archive_material(db, id))


@router.get("/{id}/related", response_model=list[MaterialResponse])
def get_related(id: str, db: Session = Depends(get_db), current_user: User | None = Depends(get_optional_user)):
    material = material_service.get_material(db, id)
    if not material or (material.publication_status != "published" and not _is_staff(current_user)):
        raise HTTPException(status_code=404, detail="Material not found")
    return material_service.get_related_materials(db, material.id, 5, published_only=not _is_staff(current_user))
