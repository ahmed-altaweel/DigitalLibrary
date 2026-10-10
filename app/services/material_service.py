from sqlalchemy.orm import Session
from ..models.material import Material, Author, Category, Tag
import uuid

def generate_slug(title: str) -> str:
    return title.lower().replace(" ", "-") + "-" + str(uuid.uuid4())[:8]

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
        created_by=user_id
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return material

def update_material(db: Session, material_id: str, data, user_id: str):
    material = get_material(db, material_id)
    if not material:
        return None
    for key, value in data.dict(exclude_unset=True).items():
        setattr(material, key, value)
    db.commit()
    db.refresh(material)
    return material

def publish_material(db: Session, material_id: str):
    material = get_material(db, material_id)
    if material:
        material.publication_status = 'published'
        from datetime import datetime, timezone
        material.published_at = datetime.now(timezone.utc)
        db.commit()
    return material

def unpublish_material(db: Session, material_id: str):
    material = get_material(db, material_id)
    if material:
        material.publication_status = 'draft'
        db.commit()
    return material

def archive_material(db: Session, material_id: str):
    material = get_material(db, material_id)
    if material:
        material.publication_status = 'archived'
        db.commit()
    return material

def delete_material(db: Session, material_id: str):
    material = get_material(db, material_id)
    if material:
        db.delete(material)
        db.commit()
    return True

def get_material(db: Session, material_id_or_slug: str, user=None):
    return db.query(Material).filter((Material.id == material_id_or_slug) | (Material.slug == material_id_or_slug)).first()

def search_materials(db: Session, query: str, filters: dict, page: int, size: int, sort: str):
    q = db.query(Material)
    if query:
        q = q.filter(Material.title.ilike(f"%{query}%"))
    if filters.get("status"):
        q = q.filter(Material.publication_status == filters["status"])
    total = q.count()
    items = q.offset((page - 1) * size).limit(size).all()
    return items, total

def get_related_materials(db: Session, material_id: str, limit: int):
    # Dummy logic
    return db.query(Material).limit(limit).all()
