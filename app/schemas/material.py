from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, date
from typing import Any, Generic, TypeVar

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int

class AuthorBase(BaseModel):
    name: str
    bio: str | None = None
    website: str | None = None

class AuthorCreate(AuthorBase):
    pass

class AuthorResponse(AuthorBase):
    id: str
    slug: str
    model_config = ConfigDict(from_attributes=True)

class CategoryBase(BaseModel):
    name: str
    description: str | None = None
    parent_id: str | None = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: str
    slug: str
    model_config = ConfigDict(from_attributes=True)

class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class TagResponse(TagBase):
    id: str
    slug: str
    model_config = ConfigDict(from_attributes=True)

class AssetBase(BaseModel):
    original_filename: str
    mime_type: str
    file_size: int
    access_policy: str = "private"
    is_primary: bool = False

class AssetResponse(AssetBase):
    id: str
    url: str | None = None
    model_config = ConfigDict(from_attributes=True)

class MaterialBase(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    content_type: str = Field(max_length=50)
    language: str = Field(default="en", max_length=10)
    publication_date: date | None = None
    isbn: str | None = Field(default=None, max_length=20)
    doi: str | None = Field(default=None, max_length=255)
    page_count: int | None = Field(default=None, ge=0)
    license_type: str | None = Field(default=None, max_length=100)
    license_notes: str | None = None
    cover_image_url: str | None = Field(default=None, max_length=500)
    external_url: str | None = Field(default=None, max_length=1000)

class MaterialCreate(MaterialBase):
    author_ids: list[str] = []
    category_ids: list[str] = []
    tag_ids: list[str] = []

class MaterialUpdate(BaseModel):
    """All fields optional so PUT behaves as a partial update."""
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    content_type: str | None = Field(default=None, max_length=50)
    language: str | None = Field(default=None, max_length=10)
    publication_date: date | None = None
    isbn: str | None = Field(default=None, max_length=20)
    doi: str | None = Field(default=None, max_length=255)
    page_count: int | None = Field(default=None, ge=0)
    license_type: str | None = Field(default=None, max_length=100)
    license_notes: str | None = None
    cover_image_url: str | None = Field(default=None, max_length=500)
    external_url: str | None = Field(default=None, max_length=1000)

class MaterialResponse(MaterialBase):
    id: str
    slug: str
    publication_status: str
    view_count: int
    download_count: int
    created_at: datetime
    published_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)

class MaterialListResponse(MaterialResponse):
    pass

class MaterialSearchParams(BaseModel):
    q: str | None = None
    content_type: str | None = None
    category_id: str | None = None
    tag_id: str | None = None
    author_id: str | None = None
    status: str | None = "published"
