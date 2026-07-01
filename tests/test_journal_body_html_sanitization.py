"""Regressionstest PR10 (SEC-9): LageJournalEntry.body_html muss immer über den
Model-Validator sanitisiert werden — auch wenn ein Schreibpfad vergisst,
sanitize_html() selbst aufzurufen (zentraler Choke-Point statt pro Router)."""
from app.models.major_incident import LageJournalEntry


def test_body_html_is_sanitized_even_without_explicit_sanitize_call():
    entry = LageJournalEntry(
        major_incident_id=1,
        category="sonstiges",
        text="Testeintrag",
        body_html='<script>alert(1)</script><p onclick="evil()">Text</p>',
    )
    assert "<script" not in (entry.body_html or "")
    assert "onclick" not in (entry.body_html or "")
    assert "<p>Text</p>" in entry.body_html


def test_body_html_allows_safe_tags():
    entry = LageJournalEntry(
        major_incident_id=1, category="sonstiges", text="x",
        body_html="<p><strong>Fett</strong> und <a href=\"https://example.org\">Link</a></p>",
    )
    assert "<strong>Fett</strong>" in entry.body_html
    assert 'href="https://example.org"' in entry.body_html


def test_body_html_none_stays_none():
    entry = LageJournalEntry(major_incident_id=1, category="sonstiges", text="x", body_html=None)
    assert entry.body_html is None


def test_body_html_reassignment_after_construction_also_sanitized():
    entry = LageJournalEntry(major_incident_id=1, category="sonstiges", text="x")
    entry.body_html = '<img src=x onerror="alert(1)">unsafe'
    assert "onerror" not in (entry.body_html or "")
    assert "<img" not in (entry.body_html or "")
