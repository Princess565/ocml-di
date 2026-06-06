from fastapi import Depends, HTTPException, status, Request, Form
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
templates = Jinja2Templates(directory="templates")

# Demo user store (replace with DB later)
USERS = {
    "doctor1": {"password": "pass123", "role": "doctor"},
    "pharma1": {"password": "pharma123", "role": "pharmacist"},
}

AUTHORIZED_ROLES = {"doctor", "pharmacist", "nurse"}

def get_current_user(token: str = Depends(oauth2_scheme)):
    # Stubbed JWT decode
    user = {"id": "doctor1", "role": "doctor"}
    if user["role"] not in AUTHORIZED_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return user

# Login route
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

def login_action(username: str = Form(...), password: str = Form(...)):
    user = USERS.get(username)
    if user and user["password"] == password:
        # In real app, issue JWT here
        return RedirectResponse(url="/clinician/dashboard", status_code=303)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
