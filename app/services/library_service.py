from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models.library import UserLibrary, ReadingList, ReadingListItem, ReadingProgress, UserBookmark, UserMaterialTag, UserNote
from ..models.material import Material


def _published_material_or_404(db: Session, material_id: str) -> Material:
    material = db.query(Material).filter(Material.id == material_id, Material.publication_status == "published").first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material


def add_to_library(db: Session, user_id: str, material_id: str):
    _published_material_or_404(db, material_id)
    existing = db.query(UserLibrary).filter(UserLibrary.user_id == user_id, UserLibrary.material_id == material_id).first()
    if existing:  # idempotent: adding twice is not an error
        return existing
    item = UserLibrary(user_id=user_id, material_id=material_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

def remove_from_library(db: Session, user_id: str, material_id: str):
    db.query(UserLibrary).filter(UserLibrary.user_id == user_id, UserLibrary.material_id == material_id).delete()
    db.commit()

def get_user_library(db: Session, user_id: str, page: int, size: int):
    q = db.query(UserLibrary).filter(UserLibrary.user_id == user_id)
    total = q.count()
    items = q.order_by(UserLibrary.added_at.desc(), UserLibrary.id).offset((page-1)*size).limit(size).all()
    return items, total

def create_reading_list(db: Session, user_id: str, data):
    rl = ReadingList(user_id=user_id, title=data.title, description=data.description, is_public=data.is_public)
    db.add(rl)
    db.commit()
    db.refresh(rl)
    return rl

def update_reading_list(db: Session, user_id: str, list_id: str, data):
    rl = db.query(ReadingList).filter(ReadingList.id == list_id, ReadingList.user_id == user_id).first()
    if rl:
        rl.title = data.title
        rl.description = data.description
        rl.is_public = data.is_public
        db.commit()
        db.refresh(rl)
    return rl

def delete_reading_list(db: Session, user_id: str, list_id: str):
    rl = db.query(ReadingList).filter(ReadingList.id == list_id, ReadingList.user_id == user_id).first()
    if rl:
        db.query(ReadingListItem).filter(ReadingListItem.reading_list_id == list_id).delete()
        db.delete(rl)
        db.commit()
        return True
    return False

def add_to_reading_list(db: Session, user_id: str, list_id: str, material_id: str, order: int, notes: str | None = None):
    rl = db.query(ReadingList).filter(ReadingList.id == list_id, ReadingList.user_id == user_id).first()
    if not rl:
        return None
    _published_material_or_404(db, material_id)
    exists = db.query(ReadingListItem).filter(
        ReadingListItem.reading_list_id == list_id, ReadingListItem.material_id == material_id
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail="Material is already in this list")
    item = ReadingListItem(reading_list_id=list_id, material_id=material_id, display_order=order, notes=notes)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

def remove_from_reading_list(db: Session, user_id: str, list_id: str, item_id: str):
    rl = db.query(ReadingList).filter(ReadingList.id == list_id, ReadingList.user_id == user_id).first()
    if rl:
        db.query(ReadingListItem).filter(ReadingListItem.id == item_id, ReadingListItem.reading_list_id == list_id).delete()
        db.commit()

def reorder_reading_list(db: Session, user_id: str, list_id: str, item_orders: list):
    rl = db.query(ReadingList).filter(ReadingList.id == list_id, ReadingList.user_id == user_id).first()
    if rl:
        for order_info in item_orders:
            item_id = order_info.get("item_id")
            order = order_info.get("order")
            item = db.query(ReadingListItem).filter(ReadingListItem.id == item_id, ReadingListItem.reading_list_id == list_id).first()
            if item:
                item.display_order = order
        db.commit()

def get_public_reading_lists(db: Session, page: int, size: int):
    q = db.query(ReadingList).filter(ReadingList.is_public == True)  # noqa: E712
    total = q.count()
    items = q.order_by(ReadingList.created_at.desc(), ReadingList.id).offset((page-1)*size).limit(size).all()
    return items, total

def get_public_reading_list(db: Session, list_id: str):
    """Returns (list, items). Items point only at published materials."""
    rl = db.query(ReadingList).filter(ReadingList.id == list_id, ReadingList.is_public == True).first()  # noqa: E712
    if not rl:
        return None, []
    items = (
        db.query(ReadingListItem)
        .join(Material, Material.id == ReadingListItem.material_id)
        .filter(ReadingListItem.reading_list_id == list_id, Material.publication_status == "published")
        .order_by(ReadingListItem.display_order, ReadingListItem.added_at)
        .all()
    )
    return rl, items

def update_reading_progress(db: Session, user_id: str, material_id: str, data):
    rp = db.query(ReadingProgress).filter(ReadingProgress.user_id == user_id, ReadingProgress.material_id == material_id).first()
    now = datetime.now(timezone.utc)
    
    if not rp:
        rp = ReadingProgress(user_id=user_id, material_id=material_id)
        db.add(rp)
        
    rp.last_read_at = now
    
    if data.current_page is not None:
        rp.current_page = data.current_page
    if data.total_pages is not None:
        rp.total_pages = data.total_pages
        
    if rp.current_page and rp.total_pages:
        rp.completion_percentage = min(100.0, max(0.0, (rp.current_page / rp.total_pages) * 100))
        
    if data.status:
        if data.status == 'in_progress' and rp.status != 'in_progress' and not rp.started_at:
            rp.started_at = now
        if data.status == 'completed' and rp.status != 'completed':
            rp.completed_at = now
            rp.completion_percentage = 100.0
        rp.status = data.status
        
    db.commit()
    db.refresh(rp)
    return rp

def get_reading_progress(db: Session, user_id: str, material_id=None):
    if material_id:
        return db.query(ReadingProgress).filter(ReadingProgress.user_id == user_id, ReadingProgress.material_id == material_id).first()
    return db.query(ReadingProgress).filter(ReadingProgress.user_id == user_id).all()

def create_bookmark(db: Session, user_id: str, material_id: str, data):
    b = UserBookmark(
        user_id=user_id,
        material_id=material_id,
        page_number=data.page_number,
        position_data=data.position_data,
        title=data.title,
        note=data.note,
        color=data.color
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return b

def update_bookmark(db: Session, user_id: str, bookmark_id: str, data):
    b = db.query(UserBookmark).filter(UserBookmark.id == bookmark_id, UserBookmark.user_id == user_id).first()
    if b:
        if data.page_number is not None:
            b.page_number = data.page_number
        if data.position_data is not None:
            b.position_data = data.position_data
        if data.title is not None:
            b.title = data.title
        if data.note is not None:
            b.note = data.note
        if data.color is not None:
            b.color = data.color
        db.commit()
    return b

def delete_bookmark(db: Session, user_id: str, bookmark_id: str):
    b = db.query(UserBookmark).filter(UserBookmark.id == bookmark_id, UserBookmark.user_id == user_id).first()
    if b:
        db.delete(b)
        db.commit()
        return True
    return False

def get_bookmarks(db: Session, user_id: str, material_id=None):
    q = db.query(UserBookmark).filter(UserBookmark.user_id == user_id)
    if material_id:
        q = q.filter(UserBookmark.material_id == material_id)
    return q.all()

def add_user_tag(db: Session, user_id: str, material_id: str, tag_name: str):
    tag_name = tag_name.strip()
    if not tag_name:
        raise HTTPException(status_code=400, detail="Tag name is required")
    _published_material_or_404(db, material_id)
    exists = db.query(UserMaterialTag).filter(
        UserMaterialTag.user_id == user_id,
        UserMaterialTag.material_id == material_id,
        UserMaterialTag.tag_name == tag_name,
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail="You already added this tag to the material")
    t = UserMaterialTag(user_id=user_id, material_id=material_id, tag_name=tag_name)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t

def remove_user_tag(db: Session, user_id: str, tag_id: str):
    t = db.query(UserMaterialTag).filter(UserMaterialTag.id == tag_id, UserMaterialTag.user_id == user_id).first()
    if t:
        db.delete(t)
        db.commit()
        return True
    return False

def get_user_tags(db: Session, user_id: str):
    return db.query(UserMaterialTag).filter(UserMaterialTag.user_id == user_id).all()

def create_note(db: Session, user_id: str, material_id: str, data):
    n = UserNote(user_id=user_id, material_id=material_id, content=data.content, page_number=data.page_number)
    db.add(n)
    db.commit()
    db.refresh(n)
    return n

def update_note(db: Session, user_id: str, note_id: str, data):
    n = db.query(UserNote).filter(UserNote.id == note_id, UserNote.user_id == user_id).first()
    if n:
        n.content = data.content
        if data.page_number is not None:
            n.page_number = data.page_number
        db.commit()
    return n

def delete_note(db: Session, user_id: str, note_id: str):
    n = db.query(UserNote).filter(UserNote.id == note_id, UserNote.user_id == user_id).first()
    if n:
        db.delete(n)
        db.commit()
        return True
    return False

def get_notes(db: Session, user_id: str, material_id=None):
    q = db.query(UserNote).filter(UserNote.user_id == user_id)
    if material_id:
        q = q.filter(UserNote.material_id == material_id)
    return q.all()