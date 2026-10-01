from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])

# POST /register, POST /login, POST /logout, POST /verify-email, GET /me
# implemented in Phase 3 (Backend) alongside the User model.
