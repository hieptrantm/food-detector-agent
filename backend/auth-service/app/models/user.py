from sqlalchemy import Column, String, Integer, TIMESTAMP, UniqueConstraint, Boolean, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String, nullable=True)
    provider = Column(String(50), nullable=False)
    provider_id = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    email_verified = Column(Boolean, default=False)
    last_login = Column(TIMESTAMP, nullable=True)

    __table_args__ = (UniqueConstraint("provider", "provider_id", name="uq_provider_provider_id"),)