from fastapi import APIRouter, Depends
from app.utils.users.roles import require_role
from app.models.user import UserRole

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.get("/me")
def me(current_user = Depends(require_role(UserRole.investor))):
    return {"message": f"Bienvenido, {current_user.email}!", "role": current_user.role}

@router.get("/admin")
def admin_panel(current_user = Depends(require_role(UserRole.admin))):
    return {"message": f"Panel de administrador activo para {current_user.email}"}

@router.get("/analytics")
def analytics_dashboard(current_user = Depends(require_role(UserRole.analyst))):
    return {"message": f"Dashboard financiero de analista visible para {current_user.email}"}
