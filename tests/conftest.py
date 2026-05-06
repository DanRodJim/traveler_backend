import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys
from typing import Generator
import uuid
from datetime import date, time, timedelta
from dotenv import load_dotenv
import logging  # ✅ Agregar

# ✅ Desactivar logs durante tests
logging.disable(logging.CRITICAL)

# Cargar variables de entorno de .env.test
load_dotenv(".env.test")

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.database.db import Base, get_db
from app.core.security import get_password_hash
from app.models.user import User
from app.models.trip import Trip, TripStatus, TripMember, MemberRole
from app.models.activity import Activity, ActivityCategory
from app.models.flight import Flight
from app.models.accommodation import Accommodation, AccommodationType
from app.models.expense import Expense, ExpenseCategory

# ✅ PostgreSQL en Docker para tests (puerto 5433)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://test_user:test_password@localhost:5433/test_travel_planner"
)

print(f"-- Using test database: {TEST_DATABASE_URL}")

# Crear engine
engine = create_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,  # Verificar conexión antes de usar
    pool_size=5,
    max_overflow=10
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Crear todas las tablas una vez al inicio de la sesión de tests
    Se ejecuta automáticamente antes de todos los tests
    """
    print("🔨 Creating test database tables...")
    Base.metadata.create_all(bind=engine)
    yield
    print("🧹 Dropping test database tables...")
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator:
    """
    Database fixture - crea transacción por test y hace rollback
    Cada test obtiene una base de datos limpia
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db) -> Generator:
    """TestClient fixture con DB de prueba"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


# --- User Fixtures ---

@pytest.fixture
def test_user(db) -> User:
    """Usuario de prueba principal"""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_user2(db) -> User:
    """Segundo usuario de prueba"""
    user = User(
        id=uuid.uuid4(),
        email="test2@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User 2",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_user3(db) -> User:
    """Tercer usuario de prueba"""
    user = User(
        id=uuid.uuid4(),
        email="test3@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User 3",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, test_user) -> dict:
    """Headers de autenticación para test_user"""
    response = client.post(
        "/api/auth/login",
        data={
            "username": test_user.email,
            "password": "testpassword123"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers2(client, test_user2) -> dict:
    """Headers de autenticación para test_user2"""
    response = client.post(
        "/api/auth/login",
        data={
            "username": test_user2.email,
            "password": "testpassword123"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# --- Trip Fixtures ---

@pytest.fixture
def test_trip(db, test_user) -> Trip:
    """Viaje de prueba"""
    trip = Trip(
        id=uuid.uuid4(),
        title="Test Trip to Japan",
        destination="Tokyo, Kyoto, Osaka",
        description="Amazing trip to Japan",
        start_date=date.today() + timedelta(days=30),
        end_date=date.today() + timedelta(days=45),
        budget=3000.00,
        currency="USD",
        status=TripStatus.PLANNING,
        owner_id=test_user.id
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


@pytest.fixture
def test_trip2(db, test_user2) -> Trip:
    """Segundo viaje de prueba (de otro usuario)"""
    trip = Trip(
        id=uuid.uuid4(),
        title="Test Trip to Paris",
        destination="Paris, France",
        description="Romantic getaway",
        start_date=date.today() + timedelta(days=60),
        end_date=date.today() + timedelta(days=75),
        budget=2500.00,
        currency="EUR",
        status=TripStatus.PLANNING,
        owner_id=test_user2.id
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


@pytest.fixture
def test_trip_member(db, test_trip, test_user2) -> TripMember:
    """Usuario 2 como miembro del viaje de usuario 1"""
    member = TripMember(
        id=uuid.uuid4(),
        trip_id=test_trip.id,
        user_id=test_user2.id,
        role=MemberRole.editor
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    
    return member


# --- Activity Fixtures ---

@pytest.fixture
def test_activity(db, test_trip, test_user) -> Activity:
    """Actividad de prueba"""
    activity = Activity(
        id=uuid.uuid4(),
        trip_id=test_trip.id,
        title="Visit Tokyo Tower",
        description="Amazing view of Tokyo",
        activity_date=date.today() + timedelta(days=35),
        start_time=time(10, 0),
        end_time=time(12, 0),
        location="Tokyo Tower",
        category=ActivityCategory.SIGHTSEEING,
        cost=25.00,
        created_by=test_user.id
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


# --- Flight Fixtures ---

@pytest.fixture
def test_flight(db, test_trip, test_user) -> Flight:
    """Vuelo de prueba"""
    flight = Flight(
        id=uuid.uuid4(),
        trip_id=test_trip.id,
        airline="Delta Airlines",
        flight_number="DL123",
        departure_airport="LAX",
        arrival_airport="NRT",
        departure_date=date.today() + timedelta(days=30),
        departure_time=time(14, 0),
        arrival_date=date.today() + timedelta(days=31),
        arrival_time=time(18, 0),
        booking_reference="ABC123",
        cost=1200.00,
        created_by=test_user.id
    )
    db.add(flight)
    db.commit()
    db.refresh(flight)
    return flight


# --- Accommodation Fixtures ---

@pytest.fixture
def test_accommodation(db, test_trip, test_user) -> Accommodation:
    """Alojamiento de prueba"""
    accommodation = Accommodation(
        id=uuid.uuid4(),
        trip_id=test_trip.id,
        name="Tokyo Hilton Hotel",
        type=AccommodationType.HOTEL,
        address="1-2-3 Shinjuku, Tokyo",
        check_in_date=date.today() + timedelta(days=31),
        check_out_date=date.today() + timedelta(days=45),
        booking_reference="HILTON123",
        cost=1500.00,
        created_by=test_user.id
    )
    db.add(accommodation)
    db.commit()
    db.refresh(accommodation)
    return accommodation


# --- Expense Fixtures ---

@pytest.fixture
def test_expense(db, test_trip, test_user) -> Expense:
    """Gasto de prueba"""
    expense = Expense(
        id=uuid.uuid4(),
        trip_id=test_trip.id,
        title="Dinner at restaurant",
        amount=85.50,
        currency="USD",
        category=ExpenseCategory.FOOD,
        expense_date=date.today() + timedelta(days=35),
        paid_by=test_user.id,
        split_between=[str(test_user.id)]
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense