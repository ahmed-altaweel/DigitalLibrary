from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer, Date, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ..core.database import Base

class Material(Base):
    __tablename__ = "materials"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=False)
    slug = Column(String(500), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    content_type = Column(String(50), nullable=False)
    language = Column(String(10), default='en')
    publication_status = Column(String(20), default='draft')
    publication_date = Column(Date, nullable=True)
    isbn = Column(String(20), nullable=True)
    doi = Column(String(255), nullable=True)
    page_count = Column(Integer, nullable=True)
    license_type = Column(String(100), nullable=True)
    license_notes = Column(Text, nullable=True)
    cover_image_url = Column(String(500), nullable=True)
    external_url = Column(String(1000), nullable=True)
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    created_by = Column(String(36), ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    published_at = Column(DateTime, nullable=True)

class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    material_id = Column(String(36), ForeignKey('materials.id'))
    storage_key = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    checksum_sha256 = Column(String(64), nullable=True)
    version = Column(Integer, default=1)
    access_policy = Column(String(20), default='private')
    is_primary = Column(Boolean, default=False)
    uploaded_by = Column(String(36), ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class Author(Base):
    __tablename__ = "authors"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True)
    bio = Column(Text, nullable=True)
    website = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class MaterialAuthor(Base):
    __tablename__ = "material_authors"
    
    material_id = Column(String(36), ForeignKey('materials.id'), primary_key=True)
    author_id = Column(String(36), ForeignKey('authors.id'), primary_key=True)
    role = Column(String(50), default='author')
    display_order = Column(Integer, default=0)

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    parent_id = Column(String(36), ForeignKey('categories.id'), nullable=True)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class MaterialCategory(Base):
    __tablename__ = "material_categories"
    
    material_id = Column(String(36), ForeignKey('materials.id'), primary_key=True)
    category_id = Column(String(36), ForeignKey('categories.id'), primary_key=True)

class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=func.now())

class MaterialTag(Base):
    __tablename__ = "material_tags"
    
    material_id = Column(String(36), ForeignKey('materials.id'), primary_key=True)
    tag_id = Column(String(36), ForeignKey('tags.id'), primary_key=True)
