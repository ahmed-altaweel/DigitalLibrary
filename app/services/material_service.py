import re
import unicodedata
import uuid

from sqlalchemy.orm import Session

from ..core.security import utcnow
from ..models.library import (
    ReadingListItem,
    ReadingProgress,
    UserBookmark,
    UserLibrary,
    UserMaterialTag,
    UserNote,
)
from ..models.material import (
    Asset,
    Material,
    MaterialAuthor,
    MaterialCategory,
    MaterialTag,
)
from ..models.suggestion import CatalogSuggestion
from ..storage.factory import get_storage

SORT_COLUMNS = {
    "created_at": Material.created_at,
    "title": Material.title,
    "published_at": Material.published_at,
    "view_count": Material.view_count,
    "download_count": Material.download_count,
}


def generate_slug(title: str) -> str:
    """Unicode-aware slug (keeps Arabic and other scripts) + short random suffix for uniqueness."""
    text = unicodedata.normalize("NFKC", title).lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_-]+", "-", text).strip("-")[:100]
    return f"{text or 'item'}-{uuid.uuid4().hex[:8]}"


def create_material(db: Session, data, user_id: str):
    material = Material(
        title=data.title,
        slug=generate_slug(data.title),
        description=data.description,
        content_type=data.content_type,
        language=data.language,
        publication_date=data.publication_date,
        isbn=data.isbn,
        doi=data.doi,
        page_count=data.page_count,
        license_type=data.license_type,
        license_notes=data.license_notes,
        cover_image_url=data.cover_image_url,
        external_url=data.external_url,
        created_by=user_id,
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


def update_material(db: Session, material_id: str, data, user_id: str):
    material = get_material(db, material_id)
    if not material:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        if value is None and key in {"title", "content_type", "language"}:
            continue  # NOT NULL columns: ignore explicit nulls
        setattr(material, key, value)
    db.commit()
    db.refresh(material)
    return material


def _set_status(db: Session, material_id: str, status: str):
    material = get_material(db, material_id)
    if not material:
        return None
    material.publication_status = status
    if status == "published":
        material.published_at = utcnow()
    db.commit()
    db.refresh(material)
    return material


def publish_material(db: Session, material_id: str):
    return _set_status(db, material_id, "published")


def unpublish_material(db: Session, material_id: str):
    return _set_status(db, material_id, "draft")


def archive_material(db: Session, material_id: str):
    return _set_status(db, material_id, "archived")


def delete_material(db: Session, material_id: str) -> bool:
    material = get_material(db, material_id)
    if not material:
        return False
    mid = material.id

    storage_keys = [k for (k,) in db.query(Asset.storage_key).filter(Asset.material_id == mid).all()]

    # Remove every row that references the material (FKs have no ON DELETE rules yet).
    for model in (
        Asset,
        MaterialAuthor,
        MaterialCategory,
        MaterialTag,
        UserLibrary,
        ReadingListItem,
        ReadingProgress,
        UserBookmark,
        UserMaterialTag,
        UserNote,
        CatalogSuggestion,
    ):
        db.query(model).filter(model.material_id == mid).delete(synchronize_session=False)
    db.delete(material)
    db.commit()

    # Only touch storage after the DB commit succeeded, so a failure never leaves dangling DB rows.
    storage = get_storage()
    for key in storage_keys:
        try:
            storage.delete(key)
        except Exception:  # orphaned file is better than failing the request
            pass
    return True


def get_material(db: Session, material_id_or_slug: str, user=None):
    return (
        db.query(Material)
        .filter((Material.id == material_id_or_slug) | (Material.slug == material_id_or_slug))
        .first()
    )


def search_materials(
    db: Session,
    query: str | None,
    filters: dict,
    page: int,
    size: int,
    sort: str = "created_at",
    descending: bool = True,
):
    q = db.query(Material)
    if query:
        like = f"%{query}%"
        q = q.filter(Material.title.ilike(like) | Material.description.ilike(like))
    if filters.get("status"):
        q = q.filter(Material.publication_status == filters["status"])
    if filters.get("content_type"):
        q = q.filter(Material.content_type == filters["content_type"])
    if filters.get("author_id"):
        q = q.filter(Material.id.in_(
            db.query(MaterialAuthor.material_id).filter(MaterialAuthor.author_id == filters["author_id"])
        ))
    if filters.get("category_id"):
        q = q.filter(Material.id.in_(
            db.query(MaterialCategory.material_id).filter(MaterialCategory.category_id == filters["category_id"])
        ))
    if filters.get("tag_id"):
        q = q.filter(Material.id.in_(
            db.query(MaterialTag.material_id).filter(MaterialTag.tag_id == filters["tag_id"])
        ))

    total = q.count()
    column = SORT_COLUMNS.get(sort, Material.created_at)
    order = column.desc() if descending else column.asc()
    items = q.order_by(order, Material.id).offset((page - 1) * size).limit(size).all()
    return items, total


def get_related_materials(db: Session, material_id: str, limit: int, published_only: bool = True):
    """Materials sharing a category or tag with the given one (never the material itself)."""
    category_ids = [c for (c,) in db.query(MaterialCategory.category_id).filter(MaterialCategory.material_id == material_id)]
    tag_ids = [t for (t,) in db.query(MaterialTag.tag_id).filter(MaterialTag.material_id == material_id)]
    if not category_ids and not tag_ids:
        return []

    related_ids = set()
    if category_ids:
        related_ids.update(
            m for (m,) in db.query(MaterialCategory.material_id).filter(MaterialCategory.category_id.in_(category_ids))
        )
    if tag_ids:
        related_ids.update(m for (m,) in db.query(MaterialTag.material_id).filter(MaterialTag.tag_id.in_(tag_ids)))
    related_ids.discard(material_id)
    if not related_ids:
        return []

    q = db.query(Material).filter(Material.id.in_(related_ids))
    if published_only:
        q = q.filter(Material.publication_status == "published")
    return q.order_by(Material.created_at.desc(), Material.id).limit(limit).all()
