from datetime import datetime
from typing import Optional
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

    skills = mapped_column(JSON, nullable=True, default=list)
    technical_skills = mapped_column(JSON, nullable=True, default=list)
    soft_skills = mapped_column(JSON, nullable=True, default=list)
    certifications = mapped_column(JSON, nullable=True, default=list)
    education = mapped_column(JSON, nullable=True, default=list)
    companies_worked = mapped_column(JSON, nullable=True, default=list)
    job_history = mapped_column(JSON, nullable=True, default=list)

    salary_current: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    expected_salary: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notice_period: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    preferred_locations = mapped_column(JSON, nullable=True, default=list)
    remote_preference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    preferred_industries = mapped_column(JSON, nullable=True, default=list)
    preferred_companies = mapped_column(JSON, nullable=True, default=list)
    target_roles = mapped_column(JSON, nullable=True, default=list)

    visa_status: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    portfolio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="profile")

    def __repr__(self):
        return f"<Profile(id={self.id}, user_id={self.user_id})>"
