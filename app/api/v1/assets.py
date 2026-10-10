from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
import uuid
import io
import hashlib
from ...core.database import get_db
from ...core.dependencies import get_current_user, get_current_editor
from ...models.material import Asset, Material
from ...models.user import User
from ...storage.factory import get_storage

router = APIRouter()
storage = get_storage()

@router.post("/materials/{material_id}/assets")
async def upload_asset(material_id: str, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_editor)):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    contents = await file.read()
    file_size = len(contents)
    sha256 = hashlib.sha256(contents).hexdigest()
    
    storage_key = f"{uuid.uuid4()}_{file.filename}"
    storage.upload(storage_key, contents, file.content_type)
    
    asset = Asset(
        material_id=material_id,
        storage_key=storage_key,
        original_filename=file.filename,
        mime_type=file.content_type,
        file_size=file_size,
        checksum_sha256=sha256,
        uploaded_by=current_user.id
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset

@router.get("/assets/{id}/download")
def download_asset(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    asset = db.query(Asset).filter(Asset.id == id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    if not storage.exists(asset.storage_key):
        raise HTTPException(status_code=404, detail="File not found in storage")
        
    data = storage.download(asset.storage_key)
    return StreamingResponse(io.BytesIO(data), media_type=asset.mime_type, headers={
        "Content-Disposition": f"attachment; filename={asset.original_filename}"
    })

@router.delete("/assets/{id}")
def delete_asset(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_editor)):
    asset = db.query(Asset).filter(Asset.id == id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    storage.delete(asset.storage_key)
    db.delete(asset)
    db.commit()
    return {"message": "Asset deleted"}
