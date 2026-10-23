from app.security import allowed_origins, is_allowed_mutation, normalize_origin

ALLOWED = {"http://localhost:3000", "http://127.0.0.1:3000"}


def test_allowed_origins_include_local_frontend() -> None:
    origins = allowed_origins()
    assert "http://localhost:3000" in origins
    assert "http://127.0.0.1:3000" in origins


def test_normalize_origin_removes_whitespace_and_trailing_slash() -> None:
    assert normalize_origin(" http://localhost:3000/ ") == "http://localhost:3000"


def test_allowed_origin_is_allowed() -> None:
    assert is_allowed_mutation("http://localhost:3000", "cross-site", ALLOWED)


def test_allowed_origin_with_trailing_slash_is_allowed() -> None:
    assert is_allowed_mutation("http://127.0.0.1:3000/", None, ALLOWED)


def test_evil_origin_is_rejected() -> None:
    assert not is_allowed_mutation("https://evil.example", None, ALLOWED)


def test_null_origin_is_rejected() -> None:
    assert not is_allowed_mutation("null", None, ALLOWED)


def test_cross_site_without_origin_is_rejected() -> None:
    assert not is_allowed_mutation(None, "cross-site", ALLOWED)


def test_server_side_request_without_origin_is_allowed() -> None:
    assert is_allowed_mutation(None, "none", ALLOWED)
    assert is_allowed_mutation(None, None, ALLOWED)
