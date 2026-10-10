from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.dependencies import get_current_editor, get_current_user
from ...schemas.material import AuthorCreate, AuthorResponse
from ...models.material import Author
import uuid

router = APIRouter()

@router.get("/", response_model=list[AuthorResponse])
def get_authors(db: Session = Depends(get_db)):
    return db.query(Author).all()

@router.post("/", response_model=AuthorResponse)
def create_author(data: AuthorCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    slug = data.name.lower().replace(" ", "-") + "-" + str(uuid.uuid4())[:8]
    author = Author(name=data.name, slug=slug, bio=data.bio, website=data.website)
    db.add(author)
    db.commit()
    db.refresh(author)
    return author

@router.put("/{id}", response_model=AuthorResponse)
def update_author(id: str, data: AuthorCreate, db: Session = Depends(get_db), current_user=Depends(get_current_editor)):
    author = db.query(Author).filter(Author.id == id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in data.dict(exclude_unset=True).items():
        setattr(author, k, v)
    db.commit()
    db.refresh(author)
    return author

@router.delete("/{id}")
def delete_author(id: str, db: Session = Depends(get_db), current_user=Depends(get_current_editor)):
    author = db.query(Author).filter(Author.id == id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(author)
    db.commit()
    return {"message": "Deleted"}
