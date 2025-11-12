#!/usr/bin/env python3
"""
Script to create sample data for the CRM dashboard
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db import SessionLocal, engine
from app.models import Base, User, Client, Commission
from app.routers.auth import get_password_hash
from decimal import Decimal
import random

def create_sample_data():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if data already exists
        if db.query(User).count() > 0:
            print("Sample data already exists!")
            return
        
        # Create sample users
        users = [
            User(
                email="admin@crm.com",
                name="Admin User",
                hashed_password=get_password_hash("admin123"),
                is_active=True
            ),
            User(
                email="john.doe@crm.com",
                name="John Doe",
                hashed_password=get_password_hash("password123"),
                is_active=True
            ),
            User(
                email="jane.smith@crm.com",
                name="Jane Smith",
                hashed_password=get_password_hash("password123"),
                is_active=True
            ),
            User(
                email="bob.wilson@crm.com",
                name="Bob Wilson",
                hashed_password=get_password_hash("password123"),
                is_active=False
            ),
        ]
        
        for user in users:
            db.add(user)
        db.commit()
        print(f"Created {len(users)} users")
        
        # Create sample clients
        clients = [
            Client(name="Tech Corp", email="contact@techcorp.com", phone="+1-555-0101"),
            Client(name="Global Industries", email="info@globalind.com", phone="+1-555-0102"),
            Client(name="StartupXYZ", email="hello@startupxyz.com", phone="+1-555-0103"),
            Client(name="Enterprise Solutions", email="sales@enterprise.com", phone="+1-555-0104"),
            Client(name="Innovation Labs", email="contact@innovlabs.com", phone="+1-555-0105"),
            Client(name="Digital Dynamics", email="team@digitaldyn.com", phone="+1-555-0106"),
            Client(name="Future Systems", email="info@futuresys.com", phone="+1-555-0107"),
            Client(name="Alpha Technologies", email="support@alphatech.com", phone="+1-555-0108"),
        ]
        
        for client in clients:
            db.add(client)
        db.commit()
        print(f"Created {len(clients)} clients")
        
        # Create sample commissions
        commission_sources = ["Website Lead", "Referral", "Cold Call", "Social Media", "Email Campaign", "Conference"]
        commissions = []
        
        client_ids = [client.id for client in clients]
        
        for _ in range(25):  # Create 25 sample commissions
            commission = Commission(
                client_id=random.choice(client_ids),
                amount=Decimal(str(round(random.uniform(100, 5000), 2))),
                source=random.choice(commission_sources)
            )
            commissions.append(commission)
        
        for commission in commissions:
            db.add(commission)
        db.commit()
        print(f"Created {len(commissions)} commissions")
        
        print("\n✅ Sample data created successfully!")
        print("\n📊 Admin Dashboard Login Credentials:")
        print("📧 Email: admin@crm.com")
        print("🔒 Password: admin123")
        print("\n🌐 Access the admin dashboard at: http://localhost:8000/admin/")
        print("📋 API Documentation at: http://localhost:8000/docs")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data()