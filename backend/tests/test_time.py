from datetime import UTC, datetime

from app.core.time import utc_now


def test_utc_now_returns_naive_utc_timestamp() -> None:
    before = datetime.now(UTC).replace(tzinfo=None)

    value = utc_now()

    after = datetime.now(UTC).replace(tzinfo=None)
    assert value.tzinfo is None
    assert before <= value <= after
