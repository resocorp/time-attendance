"""
Authentication and Authorization Module
Handles JWT tokens, password hashing, and permission checks
"""
from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr

from app.config import get_settings
from app.database import get_database

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
settings = get_settings()
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Security scheme
security = HTTPBearer()


# ==================== PYDANTIC MODELS ====================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    department: Optional[str] = None
    employee_pin: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    department: Optional[str] = None
    employee_pin: Optional[str] = None
    is_active: bool
    is_superuser: bool
    roles: List[str] = []
    permissions: List[str] = []


# ==================== PASSWORD FUNCTIONS ====================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    # Bcrypt has a 72-byte limit, truncate if necessary
    if len(password.encode('utf-8')) > 72:
        password = password[:72]
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    # Bcrypt has a 72-byte limit, truncate if necessary
    if len(plain_password.encode('utf-8')) > 72:
        plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)


# ==================== JWT FUNCTIONS ====================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        username: str = payload.get("username")
        if user_id_str is None:
            return None
        # Convert string back to int
        user_id = int(user_id_str)
        return TokenData(user_id=user_id, username=username)
    except JWTError as e:
        import logging
        logging.error(f"JWT decode error: {e}")
        return None
    except Exception as e:
        import logging
        logging.error(f"Unexpected error decoding token: {e}")
        return None


# ==================== AUTHENTICATION ====================

def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate a user with username and password"""
    db = get_database()
    user = db.get_user_by_username(username)
    
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    if not user.get("is_active"):
        return None
    
    return user


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get the current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    token_data = decode_access_token(token)
    
    if token_data is None or token_data.user_id is None:
        raise credentials_exception
    
    db = get_database()
    user = db.get_user_by_id(token_data.user_id)
    
    if user is None:
        raise credentials_exception
    
    if not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Ensure the current user is active"""
    if not current_user.get("is_active"):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# ==================== AUTHORIZATION ====================

def require_permission(permission: str):
    """Dependency to require a specific permission"""
    def permission_checker(current_user: dict = Depends(get_current_user)) -> dict:
        db = get_database()
        
        # Superusers bypass all checks
        if current_user.get("is_superuser"):
            return current_user
        
        # Check if user has the required permission
        if not db.user_has_permission(current_user["id"], permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission} required"
            )
        
        return current_user
    
    return permission_checker


def require_role(role_name: str):
    """Dependency to require a specific role"""
    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        db = get_database()
        
        # Superusers bypass all checks
        if current_user.get("is_superuser"):
            return current_user
        
        # Check if user has the required role
        user_roles = db.get_user_roles(current_user["id"])
        role_names = [role["name"] for role in user_roles]
        
        if role_name not in role_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role_name}"
            )
        
        return current_user
    
    return role_checker


def require_superuser(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency to require superuser status"""
    if not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required"
        )
    return current_user


# ==================== USER HELPERS ====================

def get_user_response(user: dict) -> UserResponse:
    """Convert database user dict to UserResponse model"""
    db = get_database()
    
    # Get user roles and permissions
    roles = db.get_user_roles(user["id"])
    role_names = [role["name"] for role in roles]
    permissions = db.get_user_permissions(user["id"])
    
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        full_name=user.get("full_name"),
        department=user.get("department"),
        employee_pin=user.get("employee_pin"),
        is_active=bool(user.get("is_active")),
        is_superuser=bool(user.get("is_superuser")),
        roles=role_names,
        permissions=permissions
    )


def create_default_admin():
    """Create a default admin user if none exists"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        db = get_database()
        
        # Check if any superuser exists
        users = db.get_all_users()
        if any(user.get("is_superuser") for user in users):
            return None
        
        # Create default admin
        admin_user = {
            "username": "admin",
            "email": "admin@example.com",
            "password_hash": hash_password("admin123"),
            "full_name": "System Administrator",
            "is_active": True,
            "is_superuser": True
        }
        
        user = db.create_user(admin_user)
        
        # Assign admin role
        admin_role = db.get_role_by_name("admin")
        if admin_role:
            db.assign_role_to_user(user["id"], admin_role["id"])
        
        return user
    except Exception as e:
        logger.error(f"Failed to create default admin: {e}")
        logger.warning("App will start without default admin - check database connection")
        return None
