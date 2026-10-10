import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.dependencies import get_current_editor, get_current_user
from ...models.material import MaterialTag, Tag
from ...schemas.material import TagCreate, TagResponse

router = APIRouter()


@router.get("/", response_model=list[TagResponse])
def get_tags(
    q: str | None = Query(None, max_length=100),
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(Tag)
    if q:
        query = query.filter(Tag.name.ilike(f"%{q}%"))
    return query.order_by(Tag.name, Tag.id).offset((page - 1) * size).limit(size).all()


@router.post("/", response_model=TagResponse, status_code=200)
def create_tag(data: TagCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Tag name is required")
    if db.query(Tag).filter(Tag.name == name).first():  # MySQL collation makes this case-insensitive
        raise HTTPException(status_code=409, detail="Tag already exists")
    slug = name.lower().replace(" ", "-") + "-" + str(uuid.uuid4())[:8]
    tag = Tag(name=name, slug=slug)
    db.add(tag)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Tag already exists")
    db.refresh(tag)
    return tag


@router.delete("/{id}")
def delete_tag(id: str, db: Session = Depends(get_db), current_user=Depends(get_current_editor)):
    tag = db.query(Tag).filter(Tag.id == id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Not found")
    db.query(MaterialTag).filter(MaterialTag.tag_id == id).delete(synchronize_session=False)
    db.delete(tag)
    db.commit()
    return {"message": "Deleted"}