# auth.py
"""
OCML-DI Auth
Real JWT authentication with bcrypt password hashing.
"""

from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, Request, Form
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY  = "ocml-di-secret-change-in-production-2025"
ALGORITHM   = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

pwd_context   = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/token")
templates     = Jinja2Templates(directory="templates")

USERS = {
    "doctor1": {"id": "doctor1", "password": pwd_context.hash("pass123"),   "role": "doctor",     "name": "Dr Efe Ikharo"},
    "pharma1": {"id": "pharma1", "password": pwd_context.hash("pharma123"), "role": "pharmacist", "name": "Pharmacist A"},
    "nurse1":  {"id": "nurse1",  "password": pwd_context.hash("nurse123"),  "role": "nurse",      "name": "Nurse B"},
    "chw1":    {"id": "chw1",    "password": pwd_context.hash("chw123"),    "role": "chw",        "name": "CHW Field Worker"},
}

AUTHORIZED_ROLES = {"doctor", "pharmacist", "nurse", "chw"}

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire    = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def authenticate_user(username: str, password: str):
    user = USERS.get(username)
    if not user or not verify_password(password, user["password"]):
        return None
    return user

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload  = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = USERS.get(username)
    if user is None or user["role"] not in AUTHORIZED_ROLES:
        raise credentials_exception
    return user

def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

def login_action(username: str = Form(...), password: str = Form(...)):
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token    = create_access_token(data={"sub": user["id"], "role": user["role"]})
    response = RedirectResponse(url="/clinician/dashboard", status_code=303)
    response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)
    return response

def login_token(username: str = Form(...), password: str = Form(...)):
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": user["id"], "role": user["role"]})
    return {"access_token": token, "token_type": "bearer", "role": user["role"], "name": user["name"]}
