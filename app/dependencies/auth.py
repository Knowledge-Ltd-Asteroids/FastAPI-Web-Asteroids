from typing import Annotated
import uuid
from fastapi import Depends, HTTPException, Response, status, Request
import jwt
from jwt.exceptions import InvalidTokenError
from app.config import get_settings
from app.models.user import User
from app.dependencies.session import SessionDep
from app.repositories.user import UserRepository


Guest_Cookie_Name = "guest_id"

def create_guest_cookie(response: Response) -> str:

    token = "guest_" + str(uuid.uuid4())
    response.set_cookie(
        key=Guest_Cookie_Name,
        value=token,
        httponly=True,
        samesite="none",
        secure=True,
    )
    return token

def is_guest_request(request: Request) -> bool:
    return request.cookies.get(Guest_Cookie_Name, "").startswith("guest_")


async def get_current_user(request:Request, db:SessionDep)->User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = request.cookies.get("access_token")

    if token is None:
        raise credentials_exception
    try:
        payload = jwt.decode(token, get_settings().secret_key, algorithms=[get_settings().jwt_algorithm])
        user_id = payload.get("sub",None)
    except InvalidTokenError as e:
        print("Invalid token error: ", e)
        raise credentials_exception

    repo = UserRepository(db)
    user = repo.get_by_id(user_id)

    if user is None:
        raise credentials_exception
    return user

async def get_current_user_or_guest(request: Request, db: SessionDep) -> User | None:

    token = request.cookies.get("access_token")
    if token:
        try:
            payload = jwt.decode(token, get_settings().secret_key, algorithms=[get_settings().jwt_algorithm])
            user_id = payload.get("sub", None)
            repo = UserRepository(db)
            user = repo.get_by_id(user_id)
            if user:
                return user
        except InvalidTokenError:
            pass
    if is_guest_request(request):
        return None  

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

async def is_logged_in(request: Request, db:SessionDep):
    try:
        await get_current_user(request, db)
        return True
    except Exception:
        return False

IsUserLoggedIn = Annotated[bool, Depends(is_logged_in)]
AuthDep = Annotated[User, Depends(get_current_user)]
GuestAuthDep = Annotated[User | None, Depends(get_current_user_or_guest)]

async def is_admin(user: User):
    return user.role == "admin"

async def is_admin_dep(user: AuthDep):
    if not await is_admin(user):
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not authorized to access this page",
            )
    return user

AdminDep = Annotated[User, Depends(is_admin_dep)]
