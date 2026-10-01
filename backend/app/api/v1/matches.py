import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Match, MatchStatus, RideStatus, User
from app.schemas.match import MatchRead, match_to_read

router = APIRouter(prefix="/matches", tags=["matches"])

TERMINAL_STATUSES = (MatchStatus.CONFIRMED, MatchStatus.REJECTED, MatchStatus.CANCELLED, MatchStatus.EXPIRED)


def _get_match_for_user(match_id: uuid.UUID, current_user: User, db: Session) -> Match:
    match = db.get(Match, match_id)
    if match is None or current_user.id not in (match.request_a.user_id, match.request_b.user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    return match


def _cancel_other_matches_for_rides(db: Session, confirmed_match: Match) -> None:
    ride_ids = (confirmed_match.request_a_id, confirmed_match.request_b_id)
    others = db.scalars(
        select(Match).where(
            Match.id != confirmed_match.id,
            or_(Match.request_a_id.in_(ride_ids), Match.request_b_id.in_(ride_ids)),
            Match.status.in_((MatchStatus.SUGGESTED, MatchStatus.A_ACCEPTED, MatchStatus.B_ACCEPTED)),
        )
    ).all()
    for other in others:
        other.status = MatchStatus.CANCELLED


@router.get("/{match_id}", response_model=MatchRead)
def get_match(
    match_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> MatchRead:
    match = _get_match_for_user(match_id, current_user, db)
    return match_to_read(match, current_user.id)


@router.post("/{match_id}/accept", response_model=MatchRead)
def accept_match(
    match_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> MatchRead:
    match = _get_match_for_user(match_id, current_user, db)
    if match.status in TERMINAL_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Match is already {match.status.value}")

    is_a = current_user.id == match.request_a.user_id
    other_already_accepted = (
        match.status == MatchStatus.B_ACCEPTED if is_a else match.status == MatchStatus.A_ACCEPTED
    )

    if other_already_accepted:
        match.status = MatchStatus.CONFIRMED
        match.request_a.status = RideStatus.MATCHED
        match.request_b.status = RideStatus.MATCHED
        _cancel_other_matches_for_rides(db, match)
    else:
        match.status = MatchStatus.A_ACCEPTED if is_a else MatchStatus.B_ACCEPTED

    db.commit()
    db.refresh(match)
    return match_to_read(match, current_user.id)


@router.post("/{match_id}/reject", response_model=MatchRead)
def reject_match(
    match_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> MatchRead:
    match = _get_match_for_user(match_id, current_user, db)
    if match.status in (MatchStatus.CONFIRMED, MatchStatus.CANCELLED, MatchStatus.EXPIRED):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Match is already {match.status.value}")

    match.status = MatchStatus.REJECTED
    db.commit()
    db.refresh(match)
    return match_to_read(match, current_user.id)
