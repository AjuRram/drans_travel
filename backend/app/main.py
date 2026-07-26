"""VoyageAI B2B travel platform API.

The single-module layout keeps the MVP easy to run and review. Production
versions should split domain services and migrations into dedicated modules.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Annotated, Any

import httpx
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, String, Text, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./voyageai.db")
JWT_SECRET = os.getenv("JWT_SECRET", "development-only-change-me")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "480"))
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Role(str, Enum):
    admin = "admin"
    agent = "agent"
    client = "client"


class RequestStatus(str, Enum):
    submitted = "submitted"
    reviewing = "reviewing"
    quoted = "quoted"
    approved = "approved"
    booked = "booked"
    cancelled = "cancelled"


class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    billing_email: Mapped[str] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    users: Mapped[list["User"]] = relationship(back_populates="organization")


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default=Role.client.value)
    phone: Mapped[str] = mapped_column(String(40), default="")
    job_title: Mapped[str] = mapped_column(String(120), default="")
    passport_number: Mapped[str] = mapped_column(String(80), default="")
    preferences: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    organization: Mapped[Organization | None] = relationship(back_populates="users")
    requests: Mapped[list["TravelRequest"]] = relationship(
        back_populates="client", foreign_keys="TravelRequest.client_id"
    )


class TravelRequest(Base):
    __tablename__ = "travel_requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    assigned_agent_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    service_type: Mapped[str] = mapped_column(String(30), index=True)
    origin: Mapped[str] = mapped_column(String(120), default="")
    destination: Mapped[str] = mapped_column(String(120))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    travelers: Mapped[int] = mapped_column(default=1)
    budget: Mapped[float] = mapped_column(Float, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    status: Mapped[str] = mapped_column(String(30), default=RequestStatus.submitted.value, index=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    notes: Mapped[str] = mapped_column(Text, default="")
    quote_amount: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    client: Mapped[User] = relationship(foreign_keys=[client_id], back_populates="requests")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="travel_request")


class Booking(Base):
    __tablename__ = "bookings"
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("travel_requests.id"), index=True)
    confirmation_code: Mapped[str] = mapped_column(String(40), unique=True)
    provider: Mapped[str] = mapped_column(String(80))
    service_type: Mapped[str] = mapped_column(String(30))
    item: Mapped[dict[str, Any]] = mapped_column(JSON)
    total_amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    status: Mapped[str] = mapped_column(String(30), default="pending_payment")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    travel_request: Mapped[TravelRequest] = relationship(back_populates="bookings")
    invoice: Mapped["Invoice | None"] = relationship(back_populates="booking", uselist=False)


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), index=True)
    provider: Mapped[str] = mapped_column(String(40), default="mock")
    provider_payment_id: Mapped[str] = mapped_column(String(100), unique=True)
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(30), default="created")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Invoice(Base):
    __tablename__ = "invoices"
    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), unique=True)
    invoice_number: Mapped[str] = mapped_column(String(40), unique=True)
    subtotal: Mapped[float] = mapped_column(Float)
    tax: Mapped[float] = mapped_column(Float)
    total: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3))
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    booking: Mapped[Booking] = relationship(back_populates="invoice")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    code: str = Field(min_length=2, max_length=40, pattern=r"^[A-Za-z0-9_-]+$")
    billing_email: EmailStr


class OrganizationOut(ORMModel):
    id: int
    name: str
    code: str
    billing_email: str
    active: bool
    created_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=160)
    password: str = Field(min_length=8)
    role: Role = Role.client
    organization_id: int | None = None
    phone: str = ""
    job_title: str = ""


class UserOut(ORMModel):
    id: int
    organization_id: int | None
    email: str
    full_name: str
    role: str
    phone: str
    job_title: str
    preferences: dict[str, Any]
    active: bool


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=160)
    phone: str | None = None
    job_title: str | None = None
    passport_number: str | None = None
    preferences: dict[str, Any] | None = None


class TravelRequestCreate(BaseModel):
    service_type: str = Field(pattern=r"^(hotel|flight|bus|cab|event|package)$")
    origin: str = ""
    destination: str = Field(min_length=2)
    start_date: date
    end_date: date
    travelers: int = Field(default=1, ge=1, le=100)
    budget: float = Field(default=0, ge=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    details: dict[str, Any] = Field(default_factory=dict)
    notes: str = ""


class TravelRequestUpdate(BaseModel):
    origin: str | None = None
    destination: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    travelers: int | None = Field(default=None, ge=1, le=100)
    budget: float | None = Field(default=None, ge=0)
    details: dict[str, Any] | None = None
    notes: str | None = None


class RequestStatusUpdate(BaseModel):
    status: RequestStatus
    quote_amount: float | None = Field(default=None, ge=0)
    assigned_agent_id: int | None = None


class TravelRequestOut(ORMModel):
    id: int
    reference: str
    client_id: int
    assigned_agent_id: int | None
    service_type: str
    origin: str
    destination: str
    start_date: date
    end_date: date
    travelers: int
    budget: float
    currency: str
    status: str
    details: dict[str, Any]
    notes: str
    quote_amount: float | None
    created_at: datetime
    updated_at: datetime


class BookingCreate(BaseModel):
    request_id: int
    provider: str = "VoyageAI Demo Inventory"
    item: dict[str, Any]
    total_amount: float = Field(gt=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)


class BookingOut(ORMModel):
    id: int
    request_id: int
    confirmation_code: str
    provider: str
    service_type: str
    item: dict[str, Any]
    total_amount: float
    currency: str
    status: str
    created_at: datetime


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 310_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, expected = stored.split("$", 1)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 310_000)
        return hmac.compare_digest(digest.hex(), expected)
    except ValueError:
        return False


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def create_token(user: User) -> str:
    expiry = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    return jwt.encode({"sub": str(user.id), "role": user.role, "exp": expiry}, JWT_SECRET, algorithm=JWT_ALGORITHM)


def current_user(token: Annotated[str, Depends(oauth2)], db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.get(User, user_id)
    if not user or not user.active:
        raise HTTPException(status_code=401, detail="User is unavailable")
    return user


def require_roles(*roles: Role):
    def dependency(user: User = Depends(current_user)) -> User:
        if user.role not in {role.value for role in roles}:
            raise HTTPException(status_code=403, detail="Insufficient permission")
        return user
    return dependency


def validate_dates(start: date, end: date) -> None:
    if end < start:
        raise HTTPException(status_code=422, detail="End date cannot be before start date")


def request_visible(db: Session, request_id: int, user: User) -> TravelRequest:
    item = db.get(TravelRequest, request_id)
    if not item:
        raise HTTPException(status_code=404, detail="Travel request not found")
    if user.role == Role.client.value and item.client_id != user.id:
        raise HTTPException(status_code=403, detail="This request belongs to another client")
    return item


def mock_inventory(service: str, origin: str, destination: str, travelers: int) -> list[dict[str, Any]]:
    base = {"flight": 6200, "hotel": 4200, "bus": 950, "cab": 1800, "event": 1500, "package": 14500}[service]
    names = {
        "flight": ["SkyJet Flex", "Indigo Demo", "AirVista Business"],
        "hotel": ["Grand Meridian", "Urban Nest", "Harbour Suites"],
        "bus": ["InterCity Plus", "NightRide Sleeper", "GreenLine"],
        "cab": ["Sedan Comfort", "SUV Business", "Airport Executive"],
        "event": ["City Experience", "Cultural Evening", "Conference Pass"],
        "package": ["Business Essentials", "City Explorer", "Premium Flex"],
    }[service]
    return [
        {
            "id": f"{service.upper()}-{index + 1}",
            "name": name,
            "provider": "VoyageAI Demo Inventory",
            "origin": origin,
            "destination": destination,
            "price": round(base * (1 + index * 0.18) * max(1, travelers), 2),
            "currency": "INR",
            "refundable": index != 1,
            "rating": round(4.7 - index * 0.3, 1),
            "details": "Demo inventory. Connect an approved supplier before real ticketing.",
        }
        for index, name in enumerate(names)
    ]


app = FastAPI(
    title="VoyageAI B2B Travel API",
    version="1.0.0",
    description="Corporate travel request, booking, payment, invoice, and reporting API.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def initialize() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.query(User).count():
            return
        org = Organization(name="Acme Corporation", code="ACME", billing_email="billing@acme.demo")
        db.add(org)
        db.flush()
        users = [
            User(email="admin@voyageai.demo", full_name="Platform Administrator", password_hash=hash_password("Admin123!"), role=Role.admin.value),
            User(email="agent@voyageai.demo", full_name="Travel Agent", password_hash=hash_password("Agent123!"), role=Role.agent.value),
            User(email="client@acme.demo", full_name="Aarav Sharma", password_hash=hash_password("Client123!"), role=Role.client.value, organization_id=org.id, phone="+91 90000 00000", job_title="Regional Manager", preferences={"seat": "aisle", "hotel": "4-star", "meal": "vegetarian"}),
        ]
        db.add_all(users)
        db.commit()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "service": "voyageai-api"}


@app.post("/api/auth/login", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    user = db.query(User).filter(func.lower(User.email) == form.username.lower()).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return {"access_token": create_token(user), "token_type": "bearer", "user": UserOut.model_validate(user).model_dump()}


@app.get("/api/auth/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@app.patch("/api/profile", response_model=UserOut)
def update_profile(payload: ProfileUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/api/organizations", response_model=list[OrganizationOut])
def organizations(_: User = Depends(require_roles(Role.admin, Role.agent)), db: Session = Depends(get_db)):
    return db.query(Organization).order_by(Organization.created_at.desc()).all()


@app.post("/api/organizations", response_model=OrganizationOut, status_code=201)
def create_organization(payload: OrganizationCreate, _: User = Depends(require_roles(Role.admin)), db: Session = Depends(get_db)):
    if db.query(Organization).filter((Organization.code == payload.code.upper()) | (Organization.name == payload.name)).first():
        raise HTTPException(status_code=409, detail="Organization name or code already exists")
    item = Organization(name=payload.name, code=payload.code.upper(), billing_email=str(payload.billing_email))
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/api/users", response_model=list[UserOut])
def users(_: User = Depends(require_roles(Role.admin, Role.agent)), db: Session = Depends(get_db)):
    return db.query(User).order_by(User.created_at.desc()).all()


@app.post("/api/users", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, _: User = Depends(require_roles(Role.admin)), db: Session = Depends(get_db)):
    if db.query(User).filter(func.lower(User.email) == str(payload.email).lower()).first():
        raise HTTPException(status_code=409, detail="Email is already registered")
    if payload.organization_id and not db.get(Organization, payload.organization_id):
        raise HTTPException(status_code=404, detail="Organization not found")
    item = User(
        **payload.model_dump(exclude={"password", "email", "role"}, mode="json"),
        email=str(payload.email).lower(),
        role=payload.role.value,
        password_hash=hash_password(payload.password),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/api/travel/search")
def travel_search(
    service: str = Query(pattern=r"^(hotel|flight|bus|cab|event|package)$"),
    origin: str = "",
    destination: str = Query(min_length=2),
    travelers: int = Query(default=1, ge=1, le=100),
    _: User = Depends(current_user),
):
    return {"provider_mode": os.getenv("TRAVEL_PROVIDER", "mock"), "results": mock_inventory(service, origin, destination, travelers)}


@app.get("/api/weather")
async def weather(latitude: float, longitude: float, _: User = Depends(current_user)):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {"latitude": latitude, "longitude": longitude, "current": "temperature_2m,weather_code"}
    try:
        async with httpx.AsyncClient(timeout=6) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError:
        return {"current": None, "notice": "Weather provider is temporarily unavailable"}


@app.get("/api/travel/requests", response_model=list[TravelRequestOut])
def list_requests(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = db.query(TravelRequest)
    if user.role == Role.client.value:
        query = query.filter(TravelRequest.client_id == user.id)
    return query.order_by(TravelRequest.created_at.desc()).all()


@app.post("/api/travel/requests", response_model=TravelRequestOut, status_code=201)
def create_request(payload: TravelRequestCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    validate_dates(payload.start_date, payload.end_date)
    item = TravelRequest(
        **payload.model_dump(),
        client_id=user.id,
        reference=f"TRV-{datetime.now():%y%m%d}-{secrets.token_hex(3).upper()}",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.patch("/api/travel/requests/{request_id}", response_model=TravelRequestOut)
def update_request(request_id: int, payload: TravelRequestUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = request_visible(db, request_id, user)
    if user.role == Role.client.value and item.status not in {RequestStatus.submitted.value, RequestStatus.reviewing.value}:
        raise HTTPException(status_code=409, detail="Only new or reviewing requests can be edited by clients")
    changes = payload.model_dump(exclude_unset=True)
    start = changes.get("start_date", item.start_date)
    end = changes.get("end_date", item.end_date)
    validate_dates(start, end)
    for key, value in changes.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@app.patch("/api/travel/requests/{request_id}/status", response_model=TravelRequestOut)
def update_status(request_id: int, payload: RequestStatusUpdate, _: User = Depends(require_roles(Role.admin, Role.agent)), db: Session = Depends(get_db)):
    item = db.get(TravelRequest, request_id)
    if not item:
        raise HTTPException(status_code=404, detail="Travel request not found")
    item.status = payload.status.value
    item.quote_amount = payload.quote_amount
    item.assigned_agent_id = payload.assigned_agent_id
    db.commit()
    db.refresh(item)
    return item


@app.post("/api/bookings", response_model=BookingOut, status_code=201)
def create_booking(payload: BookingCreate, _: User = Depends(require_roles(Role.admin, Role.agent)), db: Session = Depends(get_db)):
    request = db.get(TravelRequest, payload.request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Travel request not found")
    booking = Booking(
        **payload.model_dump(),
        service_type=request.service_type,
        confirmation_code=f"VAI-{secrets.token_hex(4).upper()}",
    )
    request.status = RequestStatus.booked.value
    db.add(booking)
    db.flush()
    tax = round(payload.total_amount * 0.18, 2)
    db.add(Invoice(
        booking_id=booking.id,
        invoice_number=f"INV-{datetime.now():%Y%m}-{booking.id:05d}",
        subtotal=payload.total_amount,
        tax=tax,
        total=round(payload.total_amount + tax, 2),
        currency=payload.currency,
    ))
    db.commit()
    db.refresh(booking)
    return booking


@app.get("/api/bookings", response_model=list[BookingOut])
def list_bookings(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = db.query(Booking).join(TravelRequest)
    if user.role == Role.client.value:
        query = query.filter(TravelRequest.client_id == user.id)
    return query.order_by(Booking.created_at.desc()).all()


@app.post("/api/payments/{booking_id}/order")
def payment_order(booking_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    request_visible(db, booking.request_id, user)
    payment = Payment(
        booking_id=booking.id,
        provider=os.getenv("PAYMENT_PROVIDER", "mock"),
        provider_payment_id=f"pay_demo_{secrets.token_hex(8)}",
        amount=booking.total_amount,
        currency=booking.currency,
    )
    db.add(payment)
    db.commit()
    return {
        "payment_id": payment.provider_payment_id,
        "provider": payment.provider,
        "amount": payment.amount,
        "currency": payment.currency,
        "checkout_mode": "sandbox",
        "notice": "No real charge is made in mock mode.",
    }


@app.post("/api/payments/{payment_id}/confirm")
def confirm_payment(payment_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.provider_payment_id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    booking = db.get(Booking, payment.booking_id)
    request_visible(db, booking.request_id, user)
    payment.status = "paid"
    booking.status = "confirmed"
    db.commit()
    return {"status": "paid", "booking_status": "confirmed"}


@app.get("/api/invoices")
def invoices(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = db.query(Invoice).join(Booking).join(TravelRequest)
    if user.role == Role.client.value:
        query = query.filter(TravelRequest.client_id == user.id)
    return [
        {
            "invoice_number": invoice.invoice_number,
            "booking_id": invoice.booking_id,
            "subtotal": invoice.subtotal,
            "tax": invoice.tax,
            "total": invoice.total,
            "currency": invoice.currency,
            "issued_at": invoice.issued_at,
        }
        for invoice in query.order_by(Invoice.issued_at.desc()).all()
    ]


@app.get("/api/reports/summary")
def report_summary(_: User = Depends(require_roles(Role.admin, Role.agent)), db: Session = Depends(get_db)):
    statuses = dict(db.query(TravelRequest.status, func.count(TravelRequest.id)).group_by(TravelRequest.status).all())
    service_types = dict(db.query(TravelRequest.service_type, func.count(TravelRequest.id)).group_by(TravelRequest.service_type).all())
    revenue = db.query(func.coalesce(func.sum(Invoice.total), 0)).scalar()
    return {
        "organizations": db.query(Organization).count(),
        "clients": db.query(User).filter(User.role == Role.client.value).count(),
        "requests": db.query(TravelRequest).count(),
        "bookings": db.query(Booking).count(),
        "invoiced_revenue": float(revenue),
        "requests_by_status": statuses,
        "requests_by_service": service_types,
    }


class ItineraryInput(BaseModel):
    destination: str
    start_date: date
    end_date: date
    interests: list[str] = Field(default_factory=list)
    budget: float = Field(default=0, ge=0)


@app.post("/api/ai/itinerary")
def itinerary(payload: ItineraryInput, _: User = Depends(current_user)):
    validate_dates(payload.start_date, payload.end_date)
    days = min((payload.end_date - payload.start_date).days + 1, 14)
    interests = payload.interests or ["local culture", "food", "landmarks"]
    schedule = []
    for index in range(days):
        current = payload.start_date + timedelta(days=index)
        focus = interests[index % len(interests)]
        schedule.append({
            "day": index + 1,
            "date": current.isoformat(),
            "morning": f"Explore a well-reviewed {focus} area in {payload.destination}",
            "afternoon": "Flexible business/leisure block with nearby transport options",
            "evening": "Local dining recommendation based on saved preferences",
        })
    return {
        "title": f"{days}-day plan for {payload.destination}",
        "schedule": schedule,
        "estimated_budget": payload.budget,
        "generated_by": "VoyageAI explainable planning engine",
        "notice": "Verify opening hours, visas, safety guidance, and availability before travel.",
    }
