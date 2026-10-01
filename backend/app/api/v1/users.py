from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])

# GET/PATCH /me, GET/PATCH /me/preferences — implemented in Phase 3.
