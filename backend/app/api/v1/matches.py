from fastapi import APIRouter

router = APIRouter(prefix="/matches", tags=["matches"])

# GET /{match_id}, POST /{match_id}/accept, POST /{match_id}/reject
# implemented in Phase 5 alongside the matching engine.
