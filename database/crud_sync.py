from typing import Optional
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session
from database.models import Student, Vacancy
from database.db import SessionLocal

def upsert_student_sync(
    *,
    full_name: str,
    phone: str,
    social_url: Optional[str],
    doc_url: str,
    file_id: Optional[str],
    message_id: Optional[int],
    channel_id: Optional[int],
) -> None:
    """Синхронный upsert (ON CONFLICT DO UPDATE) по уникальному phone."""
    with SessionLocal() as session:  # type: Session
        stmt = pg_insert(Student).values(
            full_name=full_name,
            phone=phone,
            social_url=social_url,
            doc_url=doc_url,
            file_id=file_id,
            message_id=message_id,
            channel_id=channel_id,
        ).on_conflict_do_update(
            index_elements=[Student.phone],
            set_={
                "full_name": full_name,
                "social_url": social_url,
                "doc_url": doc_url,
                "file_id": file_id,
                "message_id": message_id,
                "channel_id": channel_id,
            },
        )
        session.execute(stmt)
        session.commit()

def list_vacancies_sync() -> list[Vacancy]:
    with SessionLocal() as s:
        stmt = select(Vacancy).order_by(Vacancy.created_at.desc())
        return s.scalars(stmt).all()