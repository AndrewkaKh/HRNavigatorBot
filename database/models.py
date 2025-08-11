from datetime import datetime

from sqlalchemy import (
    Integer, String, BigInteger,
    DateTime, func, Text
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей."""

class Student(Base):
    __tablename__ = "students"

    id:           Mapped[int]    = mapped_column(Integer, primary_key=True)
    full_name:    Mapped[str]    = mapped_column(String(200), index=True)
    phone:        Mapped[str]    = mapped_column(String(32), unique=True, nullable=False)
    social_url:   Mapped[str | None] = mapped_column(String(512))
    doc_url:      Mapped[str | None] = mapped_column(String(1024))
    file_id:      Mapped[str | None] = mapped_column(String(256))
    message_id:   Mapped[int | None] = mapped_column(Integer)
    channel_id:   Mapped[int | None] = mapped_column(BigInteger)
    comments:     Mapped[str | None] = mapped_column(Text)
    created_at:   Mapped[datetime]   = mapped_column(
        DateTime, server_default=func.now()
    )

class Vacancy(Base):
    __tablename__ = "vacancies"

    name:        Mapped[str] = mapped_column(String(200), primary_key=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at:  Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )