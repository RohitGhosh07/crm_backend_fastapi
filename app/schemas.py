from pydantic import BaseModel, EmailStr
from typing import Optional
from decimal import Decimal
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str


class UserSignIn(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: int
    email: EmailStr
    name: str
    is_active: bool
    created_at: Optional[datetime]

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserRead


class ClientCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None


class ClientRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: Optional[str] = None
    created_at: Optional[datetime]

    class Config:
        orm_mode = True


class CommissionCreate(BaseModel):
    client_id: int
    amount: Decimal
    source: Optional[str] = None


class CommissionRead(BaseModel):
    id: int
    client_id: int
    amount: Decimal
    source: Optional[str] = None
    created_at: Optional[datetime]

    class Config:
        orm_mode = True
