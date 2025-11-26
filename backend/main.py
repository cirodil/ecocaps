from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
import time

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cap_user:password@database:5432/cap_collection")

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# FastAPI app
app = FastAPI(title="Cap Collection API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    class_name = Column(String, nullable=False)
    pin_code = Column(String(4), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class CapEntry(Base):
    __tablename__ = "cap_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic Models
class UserCreate(BaseModel):
    full_name: str
    class_name: str
    pin_code: str

class UserResponse(BaseModel):
    id: int
    full_name: str
    class_name: str
    pin_code: str

class CapAdd(BaseModel):
    pin_code: str

class LeaderboardEntry(BaseModel):
    full_name: str
    class_name: str
    cap_count: int

class ClassLeaderboardEntry(BaseModel):
    class_name: str
    total_caps: int

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

# Basic endpoints
@app.get("/")
def read_root():
    return {"message": "Cap Collection API", "status": "running"}

@app.get("/health")
def health_check():
    return "OK"

# API endpoints for ESP32
@app.get("/verify-pin/{pin_code}")
def verify_pin(pin_code: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.pin_code == pin_code).first()
    if user:
        return "valid"
    else:
        return "invalid"

@app.post("/add-cap")
def add_cap(cap_data: CapAdd, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.pin_code == cap_data.pin_code).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    cap_entry = CapEntry(user_id=user.id)
    db.add(cap_entry)
    db.commit()
    
    return {"message": "Cap added successfully"}

# Admin endpoints
@app.get("/users", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.pin_code == user.pin_code).first()
    if db_user:
        raise HTTPException(status_code=400, detail="PIN already exists")
    
    new_user = User(
        full_name=user.full_name,
        class_name=user.class_name,
        pin_code=user.pin_code
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(db: Session = Depends(get_db)):
    result = db.query(
        User.full_name,
        User.class_name,
        func.count(CapEntry.id).label('cap_count')
    ).join(CapEntry, User.id == CapEntry.user_id)\
     .group_by(User.id, User.full_name, User.class_name)\
     .order_by(func.count(CapEntry.id).desc())\
     .all()
    
    return [LeaderboardEntry(
        full_name=row.full_name,
        class_name=row.class_name,
        cap_count=row.cap_count
    ) for row in result]

@app.get("/class-leaderboard", response_model=List[ClassLeaderboardEntry])
def get_class_leaderboard(db: Session = Depends(get_db)):
    result = db.query(
        User.class_name,
        func.count(CapEntry.id).label('total_caps')
    ).join(CapEntry, User.id == CapEntry.user_id)\
     .group_by(User.class_name)\
     .order_by(func.count(CapEntry.id).desc())\
     .all()
    
    return [ClassLeaderboardEntry(
        class_name=row.class_name,
        total_caps=row.total_caps
    ) for row in result]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)