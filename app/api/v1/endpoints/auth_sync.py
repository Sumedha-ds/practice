"""
Authentication sync endpoint to create/update users from auth system.
This allows the Flask auth server to sync users to the FastAPI jobs database.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User

router = APIRouter(prefix="/auth-sync", tags=["Auth Sync"])


class UserSyncRequest(BaseModel):
    phone_number: str
    name: str
    city: str


@router.post("/user")
def sync_user(
    user_data: UserSyncRequest,
    db: Session = Depends(get_db),
):
    """
    Create or update a user in the jobs database after authentication.
    This is called by the auth server after successful login/onboarding.
    """
    phone = user_data.phone_number
    
    # Check if user already exists by phone number
    user = db.query(User).filter(User.phone == phone).first()
    
    if user:
        # Update existing user
        user.name = user_data.name
        user.city = user_data.city
        db.commit()
        db.refresh(user)
        
        return {
            "success": True,
            "message": "User updated successfully",
            "user_id": user.id,
            "phone": user.phone,
            "name": user.name,
            "city": user.city,
            "is_new": False
        }
    else:
        # Create new user
        new_user = User(
            name=user_data.name,
            city=user_data.city,
            phone=phone
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {
            "success": True,
            "message": "User created successfully",
            "user_id": new_user.id,
            "phone": new_user.phone,
            "name": new_user.name,
            "city": new_user.city,
            "is_new": True
        }


@router.get("/user/{phone_number}")
def get_user_by_phone(
    phone_number: str,
    db: Session = Depends(get_db),
):
    """
    Get user details by phone number.
    """
    user = db.query(User).filter(User.phone == phone_number).first()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User with phone number {phone_number} not found"
        )
    
    return {
        "success": True,
        "user_id": user.id,
        "phone": user.phone,
        "name": user.name,
        "city": user.city
    }

