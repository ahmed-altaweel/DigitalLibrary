from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.dependencies import get_current_editor, get_current_admin, get_optional_user
from ...schemas.material import MaterialCreate, MaterialUpdate, MaterialResponse, MaterialListResponse, PaginatedResponse
from ...services import material_service
from ...models.user import User

router = APIRouter()

@router.get("/", response_model=PaginatedResponse[MaterialListResponse])
def get_materials(
    q: str = None, content_type: str = None, status: str = "published",
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    filters = {"status": status, "content_type": content_type}
    items, total = material_service.search_materials(db, q, filters, page, size, "created_at")
    return {"items": items, "total": total, "page": page, "size": size, "pages": (total + size - 1) // size}

@router.get("/{id_or_slug}", response_model=MaterialResponse)
def get_material(id_or_slug: str, db: Session = Depends(get_db), current_user: User = Depends(get_optional_user)):
    material = material_service.get_material(db, id_or_slug, current_user)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    if material.publication_status != "published":
        if not current_user or not any(r.name in ["admin", "editor"] for r in current_user.roles):
            raise HTTPException(status_code=404, detail="Material not found")
    return material

@router.post("/", response_model=MaterialResponse)
def create_material(data: MaterialCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_editor)):
    return material_service.create_material(db, data, current_user.id)

@router.put("/{id}", response_model=MaterialResponse)
def update_material(id: str, data: MaterialUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_editor)):
    m = material_service.update_material(db, id, data, current_user.id)
    if not m:
        raise HTTPException(status_code=404, detail="Material not found")
    return m

@router.delete("/{id}")
def delete_material(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    success = material_service.delete_material(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Material not found")
    return {"message": "Material deleted"}

@router.post("/{id}/publish", response_model=MaterialResponse)
def publish_material(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_editor)):
    return material_service.publish_material(db, id)

@router.post("/{id}/unpublish", response_model=MaterialResponse)
def unpublish_material(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_editor)):
    return material_service.unpublish_material(db, id)

@router.post("/{id}/archive", response_model=MaterialResponse)
def archive_material(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_editor)):
    return material_service.archive_material(db, id)

@router.get("/{id}/related", response_model=list[MaterialResponse])
def get_related(id: str, db: Session = Depends(get_db)):
    return material_service.get_related_materials(db, id, 5)
