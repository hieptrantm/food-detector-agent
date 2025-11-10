from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
import jwt
from datetime import datetime, timedelta
import os
from sqlalchemy import create_engine, Column, String, Integer, TIMESTAMP, func, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import hashlib

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/authdb")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String, nullable=True)
    provider = Column(String(50), nullable=False)
    provider_id = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (UniqueConstraint("provider", "provider_id", name="uq_provider_provider_id"),)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.getenv("SECRET_KEY", "hiep-tran-thanh-mieu")
GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com" # Replace with actual client ID
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Pydantic models
class LoginRequest(BaseModel):
    email: str
    password: str
    provider: str  # google, facebook, phone
    token: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: int 
    token_type: str = "bearer"
    
class RefreshRequest(BaseModel):
    refresh_token: str
    
class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    username: str
    email: str    

def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain: str, hashed: str):
    return hash_password(plain) == hashed

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "type": "access"
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256"), expire

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/")
def root():
    return {"service": "auth-service", "status": "running"}

@app.post("/auth/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    if request.provider == "email":
        user = db.query(User).filter(User.email == request.email, User.provider == "email").first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        if not verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid password")

    elif request.provider == "google":
        if not request.provider_id:
            raise HTTPException(status_code=400, detail="Missing provider_id for Google login")
        user = db.query(User).filter(User.provider == "google", User.provider_id == request.provider_id).first()
        if not user:
            user = User(
                username=request.email.split("@")[0],
                email=request.email,
                provider="google",
                provider_id=request.provider_id,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
    else:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    access_token, access_expire = create_access_token({"sub": user.email, "provider": user.provider})
    refresh_token = create_refresh_token({"sub": user.email})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": int(access_expire.timestamp() * 1000),  # milliseconds
        "token_type": "bearer"
    }

@app.get("/auth/verify")
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {"valid": True, "email": payload.get("sub")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
@app.post("/auth/register", response_model=TokenResponse)
def register_user(request: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=request.username,
        email=request.email,
        password_hash=hash_password(request.password),
        provider="email"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token, access_expire = create_access_token({"sub": user.email, "provider": "email"})
    refresh_token = create_refresh_token({"sub": user.email})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": int(access_expire.timestamp() * 1000),
        "token_type": "bearer"
    }
    
@app.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest):
    try:
        payload = jwt.decode(request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token type")

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access_token, access_expire = create_access_token({"sub": username})

    return {
        "access_token": new_access_token,
        "refresh_token": request.refresh_token,  
        "expires_at": int(access_expire.timestamp() * 1000),
        "token_type": "bearer"
    }

@app.get("/auth/me", response_model=UserResponse)
async def get_me(user=Depends(get_current_user), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user["sub"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": db_user.username, "email": db_user.email}

@app.post("/auth/logout")
async def logout():
    return {"message": "Logged out successfully"}