from typing import Optional
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session
from database.models import Student, Vacancy
from database.db import SessionLocal
from datetime import datetime

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


def add_vacancy_sync(name: str, description: str) -> bool:
    """
    Создаёт вакансию или обновляет описание, если такая уже есть.
    Возвращает True, если создана новая запись; False, если было обновление.
    """
    with SessionLocal() as s:
        v = s.get(Vacancy, name)  # PK = name
        if v:
            v.description = description
            s.commit()
            return False  # обновили существующую
        s.add(Vacancy(name=name, description=description))
        s.commit()
        return True  # создали новую

def delete_vacancy_sync(name: str) -> bool:
    """
    Удаляет вакансию по имени. Возвращает True, если запись была удалена.
    """
    with SessionLocal() as s:
        v = s.get(Vacancy, name)
        if not v:
            return False
        s.delete(v)
        s.commit()
        return True


def add_comment_sync(student_id: int, comment: str) -> bool:
    """Добавляет комментарий к студенту с датой. Возвращает True если студент найден."""
    with SessionLocal() as s:
        student = s.get(Student, student_id)
        if not student:
            return False

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        formatted_comment = f"{timestamp}: {comment}"

        if student.comments:
            student.comments = f"{student.comments}\n{formatted_comment}"
        else:
            student.comments = formatted_comment

        s.commit()
        return True


def get_all_students_sync() -> list[Student]:
    """Возвращает всех студентов с их данными."""
    with SessionLocal() as s:
        stmt = select(Student).order_by(Student.created_at.desc())
        return list(s.scalars(stmt).all())