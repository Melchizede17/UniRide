from fastapi import APIRouter

router = APIRouter(prefix="/rides", tags=["rides"])

# POST /, GET /{ride_id}, GET /me, PATCH /{ride_id}, DELETE /{ride_id}, GET /history
# implemented in Phase 3 alongside the RideRequest model.
