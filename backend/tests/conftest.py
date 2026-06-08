"""Shared pytest fixtures."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.supplier import Category, Supplier


@pytest.fixture
def db():
    """In-memory SQLite session, rolled back after each test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def category(db):
    cat = Category(name="Бакалея", slug="grocery")
    db.add(cat)
    db.flush()
    return cat


@pytest.fixture
def supplier(db, category):
    s = Supplier(
        name="ООО МукоМол",
        description="Производство и продажа муки пшеничной и ржаной",
        city="Воронеж",
        region="Воронежская область",
        phone="+7 (473) 234-11-22",
        email="muka@mukomol.ru",
        website="mukomol.ru",
        category=category,
        min_order_amount=50000,
        min_order_unit="руб",
        has_certificates=True,
        certificate_types=["ГОСТ", "ISO 9001"],
        delivery_regions=["Москва", "ЦФО"],
        source_platform="seed",
    )
    db.add(s)
    db.flush()
    return s
