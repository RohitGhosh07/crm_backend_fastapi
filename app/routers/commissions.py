from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas
from ..db import get_db
from .auth import get_current_user

router = APIRouter(prefix="/commissions", tags=["commissions"])


@router.post("/", response_model=schemas.CommissionRead, status_code=status.HTTP_201_CREATED)
def create_commission(
    commission_in: schemas.CommissionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Check if client exists
    client = db.query(models.Client).filter(models.Client.id == commission_in.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    commission = models.Commission(
        client_id=commission_in.client_id,
        amount=commission_in.amount,
        source=commission_in.source
    )
    db.add(commission)
    db.commit()
    db.refresh(commission)
    return commission


@router.get("/", response_model=List[schemas.CommissionRead])
def list_commissions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    commissions = db.query(models.Commission).offset(skip).limit(limit).all()
    return commissions


@router.get("/{commission_id}", response_model=schemas.CommissionRead)
def get_commission(
    commission_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    commission = db.query(models.Commission).filter(models.Commission.id == commission_id).first()
    if not commission:
        raise HTTPException(status_code=404, detail="Commission not found")
    return commission


@router.get("/client/{client_id}", response_model=List[schemas.CommissionRead])
def get_client_commissions(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Check if client exists
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    commissions = db.query(models.Commission).filter(models.Commission.client_id == client_id).all()
    return commissions