from celery_app.util import parse_date


def test_parse_date_rejects_epoch_placeholder():
    assert parse_date("1970-01-01T00:00:00Z") is None
    assert parse_date("1970-12-31T23:59:59Z") is None


def test_parse_date_accepts_real_publication_date():
    assert parse_date("2026-09-13T08:00:00Z").year == 2026
