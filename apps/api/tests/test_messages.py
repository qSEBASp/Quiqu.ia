from string import Formatter

from app.analysis import messages


def _context(rule_id: str) -> dict[str, float]:
    """Valores de relleno para todos los huecos de una regla."""
    fields: set[str] = set()
    for copy in messages.CATALOG[rule_id]:
        for text in (copy.title, copy.detail, copy.recommendation):
            for _, field_name, _, _ in Formatter().parse(text):
                if field_name:
                    fields.add(field_name)
    return {field: 1.0 for field in fields}


def test_catalog_covers_every_rule():
    assert set(messages.CATALOG) == set(messages.LABELS)
    for rule_id, variants in messages.CATALOG.items():
        assert len(variants) == 3, rule_id


def test_every_variant_renders():
    for rule_id in messages.CATALOG:
        context = _context(rule_id)
        for match_id in ("demo-01", "demo-07", "demo-14"):
            copy = messages.render(rule_id, match_id, context)
            assert copy.title.strip()
            assert copy.detail.strip()
            assert copy.recommendation.strip()


def test_render_is_deterministic_per_match():
    context = _context("first_death_rate")
    first = messages.render("first_death_rate", "demo-03", context)
    second = messages.render("first_death_rate", "demo-03", context)
    assert first == second


def test_pick_index_covers_all_variants():
    indexes = {
        messages.pick_index(f"match-{number}", "first_death_rate", 3)
        for number in range(20)
    }
    assert indexes == {0, 1, 2}


def test_different_matches_get_different_text():
    context = _context("first_death_rate")
    rendered = {
        messages.render("first_death_rate", f"demo-{number:02d}", context).title
        for number in range(1, 8)
    }
    assert len(rendered) >= 2
