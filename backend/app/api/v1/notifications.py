from fastapi import APIRouter

router = APIRouter(prefix="/notifications", tags=["notifications"])

# GET /, PATCH /{id}/read — implemented in Phase 7 alongside WebSocket notifications.
