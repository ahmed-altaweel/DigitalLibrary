from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer, Float, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ..core.database import Base

class UserLibrary(Base):
    __tablename__ = "user_library"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'))
    material_id = Column(String(36), ForeignKey('materials.id'))
    added_at = Column(DateTime, default=func.now())
    
    __table_args__ = (UniqueConstraint('user_id', 'material_id', name='uq_user_library'),)
    user = relationship("User", back_populates="library_items")

class ReadingList(Base):
    __tablename__ = "reading_lists"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    user = relationship("User", back_populates="reading_lists")

class ReadingListItem(Base):
    __tablename__ = "reading_list_items"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reading_list_id = Column(String(36), ForeignKey('reading_lists.id'))
    material_id = Column(String(36), ForeignKey('materials.id'))
    display_order = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    added_at = Column(DateTime, default=func.now())
    
    __table_args__ = (UniqueConstraint('reading_list_id', 'material_id', name='uq_reading_list_item'),)

class ReadingProgress(Base):
    __tablename__ = "reading_progress"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'))
    material_id = Column(String(36), ForeignKey('materials.id'))
    current_page = Column(Integer, nullable=True)
    total_pages = Column(Integer, nullable=True)
    completion_percentage = Column(Float, default=0)
    status = Column(String(20), default='not_started')
    started_at = Column(DateTime, nullable=True)
    last_read_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    __table_args__ = (UniqueConstraint('user_id', 'material_id', name='uq_reading_progress'),)

class UserBookmark(Base):
    __tablename__ = "user_bookmarks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'))
    material_id = Column(String(36), ForeignKey('materials.id'))
    page_number = Column(Integer, nullable=True)
    position_data = Column(JSON, nullable=True)
    title = Column(String(255), nullable=True)
    note = Column(Text, nullable=True)
    color = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class UserMaterialTag(Base):
    __tablename__ = "user_material_tags"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'))
    material_id = Column(String(36), ForeignKey('materials.id'))
    tag_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (UniqueConstraint('user_id', 'material_id', 'tag_name', name='uq_user_material_tag'),)

class UserNote(Base):
    __tablename__ = "user_notes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'))
    material_id = Column(String(36), ForeignKey('materials.id'))
    content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
