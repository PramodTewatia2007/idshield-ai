from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.auth import verify_password, create_access_token, get_current_user
from app.models.models import User
from app.schemas.schemas import Token, UserResponse
from app.services.audit_service import record_audit_event

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    content_type = request.headers.get("content-type", "")
    username = ""
    password = ""
    
    if "application/json" in content_type:
        try:
            body = await request.json()
            username = body.get("username", "")
            password = body.get("password", "")
        except Exception:
            pass
    else:
        try:
            form = await request.form()
            username = str(form.get("username", ""))
            password = str(form.get("password", ""))
        except Exception:
            pass

    query = select(User).where(User.username == username)
    res = await db.execute(query)
    user = res.scalar_one_or_none()
    
    if not user or not verify_password(password, user.hashed_password):
        await record_audit_event(
            db=db,
            actor_username=username or "anonymous",
            action="LOGIN_FAILED",
            resource_type="auth",
            resource_id="session",
            outcome="FAILURE",
            details={"reason": "Invalid credentials"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive account. Contact system administrator."
        )

    access_token = create_access_token(subject=user.username, role=user.role.value)
    
    await record_audit_event(
        db=db,
        actor_username=user.username,
        action="LOGIN_SUCCESS",
        resource_type="auth",
        resource_id=str(user.id),
        outcome="SUCCESS",
        details={"role": user.role.value},
        actor_id=user.id
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_info": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value
        }
    }

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
