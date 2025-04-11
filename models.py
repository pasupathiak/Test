from sqlalchemy import Column, LargeBinary, String, Boolean, Integer, ForeignKey, Text, TIMESTAMP, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Tenant(Base):
    __tablename__ = 'tenants'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_name = Column(String(255), nullable=False)
    tenant_description = Column(Text, nullable=False)
    tenant_email = Column(String(255), unique=True, nullable=False)
    organization = Column(String(255))
    domain = Column(String(255))
    phone_number = Column(String(15), nullable=False)
    active_status = Column(String(10), default='INACTIVE')
    kb_links = Column(ARRAY(Text), default=list)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    gen_ai_services = relationship("GenAIService", back_populates="tenant", uselist=False)
    interviewer_services = relationship("InterviewerService", back_populates="tenant", uselist=False)
    database_services = relationship("DatabaseService", back_populates="tenant", uselist=False)
    cloud_services = relationship("CloudService", back_populates="tenant", uselist=False)
    users = relationship("User", back_populates="tenant")
    uploaded_files = relationship("UploadedFile", back_populates="tenant")


class GenAIService(Base):
    __tablename__ = 'gen_ai_services'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), unique=True)
    enabled_action = Column(Boolean, default=False)
    ai_provider = Column(String(100))
    ai_model = Column(String(100))
    api_key = Column(String(255))
    tts_provider = Column(String(100))
    stt_provider = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="gen_ai_services")


class InterviewerService(Base):
    __tablename__ = 'interviewer_services'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), unique=True)
    enabled_action = Column(Boolean, default=False)
    interview_model = Column(String(100))
    ai_backend = Column(String(100))
    api_key = Column(String(255))
    voice_enabled = Column(String(10))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="interviewer_services")


class DatabaseService(Base):
    __tablename__ = 'database_services'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), unique=True)
    enabled_action = Column(Boolean, default=False)
    db_type = Column(String(50))
    db_host = Column(String(255))
    db_port = Column(String(10))
    db_name = Column(String(100))
    db_username = Column(String(100))
    db_password = Column(String(255))
    file_url = Column(LargeBinary, nullable=False)  # BYTEA
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="database_services")


class CloudService(Base):
    __tablename__ = 'cloud_services'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), unique=True)
    enabled_action = Column(Boolean, default=False)
    cloud_provider = Column(String(50))
    cloud_region = Column(String(50))
    access_key_id = Column(String(255))
    secret_access_key = Column(String(255))
    service_level = Column(String(50))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="cloud_services")


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'))
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    organization = Column(String(255))
    phone_number = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="users")
    uploaded_files = relationship('UploadedFile', back_populates='user')
    credentials = relationship('UserCredential', back_populates='user', uselist=False)


class UploadedFile(Base):
    __tablename__ = 'uploaded_files'

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String(255), nullable=False)
    file_url = Column(LargeBinary, nullable=False)  # BYTEA
    file_type = Column(String(50), nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'))
    uploaded_by = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    uploader_type = Column(String(10))
    created_at = Column(TIMESTAMP, server_default=func.now())

    tenant = relationship("Tenant", back_populates="uploaded_files")
    user = relationship("User", back_populates="uploaded_files")


class UserCredential(Base):
    __tablename__ = 'user_credentials'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), unique=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255))
    role = Column(String(50), default='user')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="credentials")
    password_reset_token = relationship('PasswordResetToken', back_populates='user_credential', uselist=False)


class PasswordResetToken(Base):
    __tablename__ = 'password_reset_tokens'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_credentials_id = Column(Integer, ForeignKey('user_credentials.id', ondelete='CASCADE'), unique=True)
    token = Column(String(255), nullable=False)
    expires_at = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    user_credential = relationship('UserCredential', back_populates='password_reset_token')