from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy import String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    current_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    target_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    years_of_experience: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    # JSON fields for complex data
    skills: Mapped[Optional[List[Any]]] = mapped_column(JSON, nullable=True)
    technical_skills: Mapped[Optional[List[Any]]] = mapped_column(JSON, nullable=True)
    soft_skills: Mapped[Optional[List[Any]]] = mapped_column(JSON, nullable=True)
    certifications: Mapped[Optional[List[Any]]] = mapped_column(JSON, nullable=True)
    education: Mapped[Optional[List[Any]]] = mapped_column(JSON, nullable=True)
    companies_worked: Mapped[Optional[List[Any]]] = mapped_column(JSON, nullable=True)
    job_history: Mapped[Optional[List[Any]]] = mapped_column(JSON, nullable=True)
    
    # Salary fields
    salary_current: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    expected_salary: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notice_period: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Job preferences
    preferred_locations: Mapped[Optional[List[Any]]] = mapped_column(JSON, nullable=True)
    remote_preference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    preferred_industries: Mapped[Optional[List[Any]]] = mapped_column(JSON, nullable=True)
    preferred_companies: Mapped[Optional[List[Any]]] = mapped_column(JSON, nullable=True)
    target_roles: Mapped[Optional[List[Any]]] = mapped_column(JSON, nullable=True)
    
    # Additional info
    visa_status: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    portfolio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["User"] = relationship("User", back_populates="profile")

    def __repr__(self) -> str:
        return f"<Profile(id={self.id}, user_id={self.user_id})>"