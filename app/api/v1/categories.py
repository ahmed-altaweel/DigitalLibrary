from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.dependencies import get_current_editor
from ...schemas.material import CategoryCreate, CategoryResponse
from ...models.material import Category
import uuid

router = APIRouter()

@router.get("/", response_model=list[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()

@router.post("/", response_model=CategoryResponse)
def create_category(data: CategoryCreate, db: Session = Depends(get_db), current_user=Depends(get_current_editor)):
    slug = data.name.lower().replace(" ", "-") + "-" + str(uuid.uuid4())[:8]
    cat = Category(name=data.name, slug=slug, description=data.description, parent_id=data.parent_id)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat

@router.put("/{id}", response_model=CategoryResponse)
def update_category(id: str, data: CategoryCreate, db: Session = Depends(get_db), current_user=Depends(get_current_editor)):
    cat = db.query(Category).filter(Category.id == id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in data.dict(exclude_unset=True).items():
        setattr(cat, k, v)
    db.commit()
    db.refresh(cat)
    return cat

@router.delete("/{id}")
def delete_category(id: str, db: Session = Depends(get_db), current_user=Depends(get_current_editor)):
    cat = db.query(Category).filter(Category.id == id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(cat)
    db.commit()
    return {"message": "Deleted"}
