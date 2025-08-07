# db.py
import os
import psycopg2

from bot.config import DB_CONFIG
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base

def get_psycopg2_connection():
    return psycopg2.connect(**DB_CONFIG)

engine = create_engine(
    "postgresql+psycopg2://",
    creator=get_psycopg2_connection,
)

# Фабрика синхронных сессий
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db_sync() -> None:
    """Создать таблицы по моделям (dev-режим; на prod лучше Alembic)."""
    Base.metadata.create_all(engine)