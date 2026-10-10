from pydantic import BaseModel, ConfigDict
from datetime import datetime

class LibraryItemResponse(BaseModel):
    id: str
    user_id: str
    material_id: str
    added_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ReadingListBase(BaseModel):
    title: str
    description: str | None = None
    is_public: bool = False

class ReadingListCreate(ReadingListBase):
    pass

class ReadingListUpdate(ReadingListBase):
    pass

class ReadingListResponse(ReadingListBase):
    id: str
    created_at: datetime
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)

class ReadingListItemAdd(BaseModel):
    material_id: str
    display_order: int = 0
    notes: str | None = None

class ReadingProgressUpdate(BaseModel):
    current_page: int | None = None
    total_pages: int | None = None
    completion_percentage: float = 0
    status: str = "not_started"

class ReadingProgressResponse(ReadingProgressUpdate):
    id: str
    material_id: str
    started_at: datetime | None = None
    last_read_at: datetime | None = None
    completed_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)

class BookmarkBase(BaseModel):
    page_number: int | None = None
    title: str | None = None
    note: str | None = None
    color: str | None = None
    position_data: dict | None = None

class BookmarkCreate(BookmarkBase):
    pass

class BookmarkUpdate(BookmarkBase):
    pass

class BookmarkResponse(BookmarkBase):
    id: str
    material_id: str
    created_at: datetime
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)

class UserTagCreate(BaseModel):
    tag_name: str

class UserNoteBase(BaseModel):
    content: str
    page_number: int | None = None

class UserNoteCreate(UserNoteBase):
    pass

class UserNoteUpdate(UserNoteBase):
    pass

class UserNoteResponse(UserNoteBase):
    id: str
    material_id: str
    created_at: datetime
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)
