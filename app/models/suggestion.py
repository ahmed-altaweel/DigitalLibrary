from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
import uuid
from ..core.database import Base

class CatalogSuggestion(Base):
    __tablename__ = "catalog_suggestions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    material_id = Column(String(36), ForeignKey('materials.id'))
    submitted_by = Column(String(36), ForeignKey('users.id'))
    suggestion_type = Column(String(50), nullable=False)
    field_name = Column(String(100), nullable=True)
    current_value = Column(Text, nullable=True)
    proposed_value = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(String(20), default='pending')
    reviewed_by = Column(String(36), ForeignKey('users.id'), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(String(36), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now())
