import re
import unicodedata
import uuid

from fastapi import HTTPException
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
    Author,
    Category,
    Material,
    MaterialAuthor,
    MaterialCategory,
    MaterialTag,
    Tag,
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


def _unique_existing_ids(db: Session, model, ids, label: str) -> list[str]:
    """De-duplicate ids and make sure every one exists (400 instead of a DB 500)."""
    ids = list(dict.fromkeys(ids or []))
    if ids and db.query(model.id).filter(model.id.in_(ids)).count() != len(ids):
        raise HTTPException(status_code=400, detail=f"Unknown {label} id")
    return ids


def create_material(db: Session, data, user_id: str, publish: bool = False):
    """Staff pass publish=True; everyone else creates a draft that an editor must publish."""
    author_ids = _unique_existing_ids(db, Author, getattr(data, "author_ids", None), "author")
    category_ids = _unique_existing_ids(db, Category, getattr(data, "category_ids", None), "category")
    tag_ids = _unique_existing_ids(db, Tag, getattr(data, "tag_ids", None), "tag")

    material = Material(
        title=data.title,
        slug=generate_slug(data.title),
        description=data.description,
        content_type=data.content_type,
        language=data.language,
        publication_status="published" if publish else "draft",
        published_at=utcnow() if publish else None,
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
    db.flush()

    for order, aid in enumerate(author_ids):
        db.add(MaterialAuthor(material_id=material.id, author_id=aid, display_order=order))
    for cid in category_ids:
        db.add(MaterialCategory(material_id=material.id, category_id=cid))
    for tid in tag_ids:
        db.add(MaterialTag(material_id=material.id, tag_id=tid))

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


def increment_view(db: Session, material_id: str):
    db.query(Material).filter(Material.id == material_id).update(
        {Material.view_count: Material.view_count + 1}, synchronize_session=False
    )
    db.commit()


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


def get_material_relations(db: Session, material_id: str, include_private_assets: bool = False) -> dict:
    """Authors, categories, tags and downloadable files of one material."""
    authors = (
        db.query(Author)
        .join(MaterialAuthor, MaterialAuthor.author_id == Author.id)
        .filter(MaterialAuthor.material_id == material_id)
        .order_by(MaterialAuthor.display_order, Author.name)
        .all()
    )
    categories = (
        db.query(Category)
        .join(MaterialCategory, MaterialCategory.category_id == Category.id)
        .filter(MaterialCategory.material_id == material_id)
        .order_by(Category.name)
        .all()
    )
    tags = (
        db.query(Tag)
        .join(MaterialTag, MaterialTag.tag_id == Tag.id)
        .filter(MaterialTag.material_id == material_id)
        .order_by(Tag.name)
        .all()
    )
    aq = db.query(Asset).filter(Asset.material_id == material_id)
    if not include_private_assets:
        aq = aq.filter(Asset.access_policy != "private")
    assets = aq.order_by(Asset.is_primary.desc(), Asset.created_at, Asset.id).all()
    return {"authors": authors, "categories": categories, "tags": tags, "assets": assets}


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
    if filters.get("created_by"):
        q = q.filter(Material.created_by == filters["created_by"])
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