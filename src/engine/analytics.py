"""Basic analytics — structured logging for key events."""
import logging
from datetime import datetime, timezone

logger = logging.getLogger("analytics")

# Event types
EVENT_MESSAGE_SENT = "message_sent"
EVENT_COACH_RESPONSE = "coach_response"
EVENT_ONBOARDING_COMPLETED = "onboarding_completed"
EVENT_FEEDBACK_GIVEN = "feedback_given"
EVENT_SESSION_SUMMARIZED = "session_summarized"
EVENT_PUSH_SENT = "push_sent"
EVENT_PUSH_FAILED = "push_failed"


def track_event(event_type: str, user_id: str, **kwargs):
    """Logs a structured analytics event."""
    logger.info(
        event_type,
        extra={
            "event": event_type,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **kwargs,
        },
    )


def track_message_sent(user_id: str, message_length: int):
    track_event(EVENT_MESSAGE_SENT, user_id, message_length=message_length)


def track_coach_response(user_id: str, tokens_in: int, tokens_out: int, cost: float):
    track_event(EVENT_COACH_RESPONSE, user_id,
                tokens_in=tokens_in, tokens_out=tokens_out, cost=cost)


def track_onboarding_completed(user_id: str, sport: str):
    track_event(EVENT_ONBOARDING_COMPLETED, user_id, sport=sport)


def track_feedback_given(user_id: str, feedback_type: str, message_id: str):
    track_event(EVENT_FEEDBACK_GIVEN, user_id,
                feedback_type=feedback_type, message_id=message_id)


def track_session_summarized(user_id: str, nb_messages: int):
    track_event(EVENT_SESSION_SUMMARIZED, user_id, nb_messages=nb_messages)
