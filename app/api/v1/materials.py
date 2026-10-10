from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.dependencies import get_current_admin, get_current_editor, get_current_user, get_optional_user, user_has_role
from ...models.user import User
from ...schemas.material import (
    AssetPublic,
    AuthorResponse,
    CategoryResponse,
    MaterialCreate,
    MaterialDetailResponse,
    MaterialListResponse,
    MaterialResponse,
    MaterialUpdate,
    PaginatedResponse,
    TagResponse,
)
from ...services import material_service

router = APIRouter()


def _is_staff(user: User | None) -> bool:
    return user_has_role(user, "admin", "editor")


def _is_owner(material, user: User | None) -> bool:
    return user is not None and material.created_by == user.id


def _can_view(material, user: User | None) -> bool:
    return material.publication_status == "published" or _is_staff(user) or _is_owner(material, user)


def _page(items, total, page, size):
    return {"items": items, "total": total, "page": page, "size": size, "pages": (total + size - 1) // size}


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
    return _page(items, total, page, size)


# NOTE: must stay above "/{id_or_slug}" so "mine" is not treated as a slug.
@router.get("/mine", response_model=PaginatedResponse[MaterialListResponse])
def get_my_materials(
    status: Literal["draft", "published", "archived"] | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Materials created by the current user, in any status (members' submissions start as drafts)."""
    items, total = material_service.search_materials(
        db, None, {"created_by": current_user.id, "status": status}, page, size
    )
    return _page(items, total, page, size)


@router.get("/{id_or_slug}", response_model=MaterialDetailResponse)
def get_material(id_or_slug: str, db: Session = Depends(get_db), current_user: User | None = Depends(get_optional_user)):
    material = material_service.get_material(db, id_or_slug, current_user)
    if not material or not _can_view(material, current_user):
        raise HTTPException(status_code=404, detail="Material not found")
    rel = material_service.get_material_relations(
        db, material.id, include_private_assets=_is_staff(current_user) or _is_owner(material, current_user)
    )
    detail = MaterialDetailResponse.model_validate(material)
    detail.authors = [AuthorResponse.model_validate(a) for a in rel["authors"]]
    detail.categories = [CategoryResponse.model_validate(c) for c in rel["categories"]]
    detail.tags = [TagResponse.model_validate(t) for t in rel["tags"]]
    detail.assets = [AssetPublic.model_validate(a) for a in rel["assets"]]
    return detail


@router.post("/{id}/view")
def register_view(id: str, db: Session = Depends(get_db)):
    """Call once when the user opens the material page; increments view_count."""
    material = material_service.get_material(db, id)
    if not material or material.publication_status != "published":
        raise HTTPException(status_code=404, detail="Material not found")
    material_service.increment_view(db, material.id)
    db.refresh(material)
    return {"view_count": material.view_count}


@router.post("/", response_model=MaterialResponse)
def create_material(data: MaterialCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Staff publish immediately; members' submissions are drafts awaiting an editor.
    return material_service.create_material(db, data, current_user.id, publish=_is_staff(current_user))


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
    if not material or not _can_view(material, current_user):
        raise HTTPException(status_code=404, detail="Material not found")
    return material_service.get_related_materials(db, material.id, 5, published_only=not _is_staff(current_user))