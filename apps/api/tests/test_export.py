from app.routers.export import _csv_safe


def test_formula_prefixes_are_neutralized() -> None:
    for value in ("=1+1", "+SUM(A1)", "-2", "@cmd", "\tfoo", "\rbar"):
        assert _csv_safe(value) == "'" + value


def test_normal_values_are_unchanged() -> None:
    assert _csv_safe("Ascent") == "Ascent"
    assert _csv_safe("5-13") == "5-13"
    assert _csv_safe(5) == 5
    assert _csv_safe(None) is None
