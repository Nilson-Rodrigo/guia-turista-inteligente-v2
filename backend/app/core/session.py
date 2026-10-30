from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import uuid4


VISITOR_TTL = timedelta(hours=2)


@dataclass
class SessionRecord:
    user_id: str
    profile: dict[str, object]
    expires_at: datetime | None = None


sessions: dict[str, SessionRecord] = {}


def create_visitor() -> SessionRecord:
    user_id = f"visitante-{uuid4().hex}"
    record = SessionRecord(
        user_id=user_id,
        profile={
            "id": user_id,
            "nome": "Viajante Convidado",
            "email": "visitante@local",
            "foto": "",
            "visitante": True,
        },
        expires_at=datetime.now(timezone.utc) + VISITOR_TTL,
    )
    sessions[user_id] = record
    return record


def get_session(user_id: str) -> SessionRecord | None:
    record = sessions.get(user_id)
    if not record:
        return None
    if record.expires_at and record.expires_at <= datetime.now(timezone.utc):
        sessions.pop(user_id, None)
        return None
    return record


def delete_session(user_id: str) -> None:
    sessions.pop(user_id, None)
