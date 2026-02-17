"""SEO module models."""
from sqlalchemy import Column, String, ForeignKey, Index, Integer, Float, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class SEOProject(Base):
    """SEO project tracking."""
    __tablename__ = "seo_projects"
    
    # Tenant isolation
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False)
    target_country = Column(String(10), default="US", nullable=False)
    target_language = Column(String(10), default="en", nullable=False)
    
    # Status
    status = Column(String(20), default="active", nullable=False)  # active, paused, archived
    
    # Relationships
    tenant = relationship("Tenant")
    keywords = relationship("SEOKeyword", back_populates="project", cascade="all, delete-orphan")
    audits = relationship("SEOAudit", back_populates="project", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_seo_projects_tenant_status", "tenant_id", "status"),
    )


class SEOKeyword(Base):
    """SEO keyword tracking."""
    __tablename__ = "seo_keywords"
    
    project_id = Column(UUID(as_uuid=True), ForeignKey("seo_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    keyword = Column(String(255), nullable=False)
    search_volume = Column(Integer, default=0, nullable=False)
    difficulty = Column(Integer, default=0, nullable=False)  # 0-100
    current_rank = Column(Integer, nullable=True)
    target_url = Column(String(500), nullable=True)
    
    # Relationships
    project = relationship("SEOProject", back_populates="keywords")
    rank_history = relationship("KeywordRankHistory", back_populates="keyword", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_seo_keywords_project_keyword", "project_id", "keyword", unique=True),
    )


class KeywordRankHistory(Base):
    """Historical rank tracking for keywords."""
    __tablename__ = "keyword_rank_history"
    
    keyword_id = Column(UUID(as_uuid=True), ForeignKey("seo_keywords.id", ondelete="CASCADE"), nullable=False, index=True)
    
    rank = Column(Integer, nullable=True)
    url = Column(String(500), nullable=True)
    search_volume = Column(Integer, default=0, nullable=False)
    
    # Relationship
    keyword = relationship("SEOKeyword", back_populates="rank_history")
    
    __table_args__ = (
        Index("ix_keyword_rank_history_keyword_created", "keyword_id", "created_at"),
    )


class SEOAudit(Base):
    """SEO audit results."""
    __tablename__ = "seo_audits"
    
    project_id = Column(UUID(as_uuid=True), ForeignKey("seo_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    audit_type = Column(String(50), nullable=False)  # technical, content, backlinks, performance
    score = Column(Float, default=0.0, nullable=False)  # 0-100
    
    # Audit results (JSONB)
    results = Column(JSONB, default={}, nullable=False)
    
    # Relationships
    project = relationship("SEOProject", back_populates="audits")
    issues = relationship("SEOIssue", back_populates="audit", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_seo_audits_project_created", "project_id", "created_at"),
    )


class SEOIssue(Base):
    """SEO issues found in audits."""
    __tablename__ = "seo_issues"
    
    audit_id = Column(UUID(as_uuid=True), ForeignKey("seo_audits.id", ondelete="CASCADE"), nullable=False, index=True)
    
    severity = Column(String(20), nullable=False)  # critical, high, medium, low
    issue_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    affected_url = Column(String(500), nullable=True)
    
    # Resolution
    status = Column(String(20), default="open", nullable=False)  # open, in_progress, resolved, ignored
    
    # Relationship
    audit = relationship("SEOAudit", back_populates="issues")
    
    __table_args__ = (
        Index("ix_seo_issues_audit_status", "audit_id", "status"),
    )
