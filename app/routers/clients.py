from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas
from ..db import get_db
from .auth import get_current_user

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("/", response_model=schemas.ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(
    client_in: schemas.ClientCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Check existing email
    existing = db.query(models.Client).filter(models.Client.email == client_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Client with this email already exists")
    client = models.Client(name=client_in.name, email=client_in.email, phone=client_in.phone)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/", response_model=List[schemas.ClientRead])
def list_clients(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    clients = db.query(models.Client).offset(skip).limit(limit).all()
    return clients


@router.get("/{client_id}", response_model=schemas.ClientRead)
def get_client(
    client_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client
