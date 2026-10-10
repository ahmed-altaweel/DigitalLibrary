import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.dependencies import get_current_editor
from ...models.material import Category, MaterialCategory
from ...schemas.material import CategoryCreate, CategoryResponse

router = APIRouter()


def _check_parent(db: Session, parent_id: str | None, own_id: str | None = None):
    if not parent_id:
        return
    if parent_id == own_id:
        raise HTTPException(status_code=400, detail="A category cannot be its own parent")
    if not db.query(Category.id).filter(Category.id == parent_id).first():
        raise HTTPException(status_code=400, detail="Parent category not found")


@router.get("/", response_model=list[CategoryResponse])
def get_categories(
    q: str | None = Query(None, max_length=255),
    page: int = Query(1, ge=1),
    size: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(Category)
    if q:
        query = query.filter(Category.name.ilike(f"%{q}%"))
    return query.order_by(Category.display_order, Category.name, Category.id).offset((page - 1) * size).limit(size).all()


@router.post("/", response_model=CategoryResponse)
def create_category(data: CategoryCreate, db: Session = Depends(get_db), current_user=Depends(get_current_editor)):
    _check_parent(db, data.parent_id)
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
    _check_parent(db, data.parent_id, own_id=id)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(cat, k, v)
    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/{id}")
def delete_category(id: str, db: Session = Depends(get_db), current_user=Depends(get_current_editor)):
    cat = db.query(Category).filter(Category.id == id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Not found")
    if db.query(Category.id).filter(Category.parent_id == id).first():
        raise HTTPException(status_code=409, detail="Category has sub-categories; move or delete them first")
    db.query(MaterialCategory).filter(MaterialCategory.category_id == id).delete(synchronize_session=False)
    db.delete(cat)
    db.commit()
    return {"message": "Deleted"}