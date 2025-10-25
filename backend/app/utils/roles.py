from fastapi import Depends, HTTPException, status
from app.utils.user import get_current_user
from app.models.user import UserRole


# Jerarchical role levels
ROLE_LEVEL = {
    UserRole.admin: 3,
    UserRole.analyst: 2,
    UserRole.investor: 1,
    UserRole.support: 2
}

def require_role(required_role: UserRole):
    def role_checker(current_user = Depends(get_current_user)):
        user_role = current_user.role

        if ROLE_LEVEL[user_role] < ROLE_LEVEL[required_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: {user_role} role cannot access this resource."
            )
        return current_user
    return role_checker