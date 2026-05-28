from app.core.retry import RetryPolicy, with_retry


def test_with_retry_succeeds_after_transient_failure() -> None:
    attempts = {"count": 0}

    def action() -> str:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("transient")
        return "ok"

    retries: list[int] = []

    def on_retry(attempt: int, _: Exception) -> None:
        retries.append(attempt)

    result = with_retry(action, on_retry=on_retry, policy=RetryPolicy(attempts=2, base_delay_seconds=0))

    assert result == "ok"
    assert attempts["count"] == 2
    assert retries == [1]


def test_with_retry_raises_after_max_attempts() -> None:
    attempts = {"count": 0}

    def action() -> None:
        attempts["count"] += 1
        raise RuntimeError("still failing")

    retries: list[int] = []

    def on_retry(attempt: int, _: Exception) -> None:
        retries.append(attempt)

    try:
        with_retry(action, on_retry=on_retry, policy=RetryPolicy(attempts=3, base_delay_seconds=0))
        raise AssertionError("expected RuntimeError")
    except RuntimeError as exc:
        assert str(exc) == "still failing"

    assert attempts["count"] == 3
    assert retries == [1, 2]
