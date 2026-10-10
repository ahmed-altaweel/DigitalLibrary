import hashlib
import io
import os
import re
import uuid
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ...core.config import get_settings
from ...core.database import get_db
from ...core.dependencies import get_current_editor, get_optional_user, user_has_role
from ...models.material import Asset, Material
from ...models.user import User
from ...storage.factory import get_storage

router = APIRouter()
storage = get_storage()
settings = get_settings()

ACCESS_POLICIES = {"public", "members", "private"}
CHUNK_SIZE = 1024 * 1024

MIME_BY_EXT = {
    "pdf": "application/pdf",
    "epub": "application/epub+zip",
    "txt": "text/plain",
    "md": "text/markdown",
}


def _clean_filename(name: str | None) -> str:
    name = (name or "file").replace("\\", "/").split("/")[-1]
    name = re.sub(r"[\x00-\x1f\x7f]", "", name).strip().strip(".")
    return (name or "file")[:255]


def _looks_like(ext: str, head: bytes) -> bool:
    """Cheap content sniffing so the extension can't be used to smuggle other file types."""
    if ext == "pdf":
        return head.startswith(b"%PDF-")
    if ext == "epub":
        return head.startswith(b"PK\x03\x04")
    if ext in {"txt", "md"}:
        if b"\x00" in head:
            return False
        try:
            head.decode("utf-8")
        except UnicodeDecodeError as e:
            # The sample may end in the middle of a multi-byte character.
            return e.start >= len(head) - 3
        return True
    return False


def _content_disposition(filename: str) -> str:
    ascii_name = re.sub(r'[^A-Za-z0-9._-]', "_", filename.encode("ascii", "ignore").decode() or "download")
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename, safe='')}"


@router.post("/materials/{material_id}/assets")
def upload_asset(
    material_id: str,
    file: UploadFile = File(...),
    access_policy: str = Form("members"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_editor),
):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    if access_policy not in ACCESS_POLICIES:
        raise HTTPException(status_code=400, detail=f"access_policy must be one of: {', '.join(sorted(ACCESS_POLICIES))}")

    original_filename = _clean_filename(file.filename)
    ext = os.path.splitext(original_filename)[1].lower().lstrip(".")
    if ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type '.{ext}' is not allowed. Allowed: {', '.join(sorted(settings.allowed_extensions))}",
        )

    # Read in chunks and stop as soon as the size limit is exceeded.
    buffer = bytearray()
    while True:
        chunk = file.file.read(CHUNK_SIZE)
        if not chunk:
            break
        buffer.extend(chunk)
        if len(buffer) > settings.max_upload_bytes:
            raise HTTPException(
                status_code=413, detail=f"File too large (max {settings.MAX_UPLOAD_SIZE_MB} MB)"
            )
    contents = bytes(buffer)
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")
    if not _looks_like(ext, contents[:8192]):
        raise HTTPException(status_code=400, detail="File content does not match its extension")

    sha256 = hashlib.sha256(contents).hexdigest()
    mime_type = MIME_BY_EXT.get(ext, "application/octet-stream")
    # The client-supplied filename is never used in the storage key.
    storage_key = f"{uuid.uuid4()}.{ext}"
    storage.upload(storage_key, contents, mime_type)

    asset = Asset(
        material_id=material_id,
        storage_key=storage_key,
        original_filename=original_filename,
        mime_type=mime_type,
        file_size=len(contents),
        checksum_sha256=sha256,
        access_policy=access_policy,
        uploaded_by=current_user.id,
    )
    db.add(asset)
    try:
        db.commit()
    except Exception:
        db.rollback()
        storage.delete(storage_key)
        raise
    db.refresh(asset)
    return asset


@router.get("/assets/{id}/download")
def download_asset(
    id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    asset = db.query(Asset).filter(Asset.id == id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    material = db.query(Material).filter(Material.id == asset.material_id).first()
    is_staff = user_has_role(current_user, "admin", "editor")
    if not is_staff:
        # Unpublished material and its files are invisible to everyone but staff.
        if not material or material.publication_status != "published":
            raise HTTPException(status_code=404, detail="Asset not found")
        if asset.access_policy == "private":
            raise HTTPException(status_code=403, detail="This file is not available for download")
        if asset.access_policy != "public" and current_user is None:
            raise HTTPException(status_code=401, detail="Not authenticated")

    if not storage.exists(asset.storage_key):
        raise HTTPException(status_code=404, detail="File not found in storage")

    data = storage.download(asset.storage_key)
    if material is not None:
        db.query(Material).filter(Material.id == material.id).update(
            {Material.download_count: Material.download_count + 1}
        )
        db.commit()
    return StreamingResponse(
        io.BytesIO(data),
        media_type=asset.mime_type,
        headers={
            "Content-Disposition": _content_disposition(asset.original_filename),
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.delete("/assets/{id}")
def delete_asset(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_editor)):
    asset = db.query(Asset).filter(Asset.id == id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    storage_key = asset.storage_key
    db.delete(asset)
    db.commit()
    storage.delete(storage_key)
    return {"message": "Asset deleted"}
