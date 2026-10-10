from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.dependencies import get_current_editor
from ...schemas.material import TagCreate, TagResponse
from ...models.material import Tag
import uuid

router = APIRouter()

@router.get("/", response_model=list[TagResponse])
def get_tags(db: Session = Depends(get_db)):
    return db.query(Tag).all()

@router.post("/", response_model=TagResponse)
def create_tag(data: TagCreate, db: Session = Depends(get_db), current_user=Depends(get_current_editor)):
    slug = data.name.lower().replace(" ", "-") + "-" + str(uuid.uuid4())[:8]
    tag = Tag(name=data.name, slug=slug)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag

@router.delete("/{id}")
def delete_tag(id: str, db: Session = Depends(get_db), current_user=Depends(get_current_editor)):
    tag = db.query(Tag).filter(Tag.id == id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(tag)
    db.commit()
    return {"message": "Deleted"}
