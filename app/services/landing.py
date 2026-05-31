"""Inhalte & Bilder der öffentlichen Startseite (einfaches CMS via SystemSettings).

Texte werden als Key-Value-Paare mit dem Präfix ``landing.`` in der Tabelle
``system_settings`` gespeichert; Bilder liegen unter ``app_storage/landing/`` und
ihr Dateiname wird unter ``landing.img.<slug>`` referenziert. Nur Systemadmins
dürfen die Inhalte über ``/admin/startseite`` pflegen.
"""
import logging
from datetime import UTC, datetime
from pathlib import Path

from app.models.master import SystemSettings

logger = logging.getLogger("einsatzleiter.landing")

LANDING_DIR = Path("app_storage/landing")
SETTINGS_PREFIX = "landing."
IMG_PREFIX = "landing.img."

# Pflegbare Bild-Slots (Slug → Label im Admin-Formular)
IMAGE_SLUGS: dict[str, str] = {
    "hero": "Hero-Bild (Dashboard / Mockup)",
    "leitwagen": "Einsatzleitwagen / Stimmungsbild",
}

# Editierbare Textfelder mit deutschen Default-Inhalten.
TEXT_DEFAULTS: dict[str, str] = {
    "hero_title": "Digitale Einsatzleitung",
    "hero_highlight": "in Echtzeit.",
    "hero_subtitle": "Das digitale Hilfswerkzeug für Feuerwehren und Rettungskräfte. "
                     "Behalten Sie den Überblick, wenn jede Sekunde zählt – mobil, "
                     "sicher und für den Ernstfall gemacht.",
    "features_heading": "Gemacht für den Ernstfall",
    "feature_1_title": "Echtzeit-Fahrzeugübersicht",
    "feature_1_desc": "FMS-Status und Mannschaftsstärke jedes Fahrzeugs auf einen Blick – "
                      "live auf jedem Gerät synchronisiert.",
    "feature_2_title": "Auftrags-Management",
    "feature_2_desc": "Übersichtliche Kanban-Boards: Aufträge zuweisen, priorisieren und den "
                      "Fortschritt jederzeit verfolgen.",
    "feature_3_title": "Echtzeit-Meldungen",
    "feature_3_desc": "Lagemeldungen und Statusupdates sekundenschnell direkt vom Einsatzort.",
    "feature_4_title": "Atemschutz-Überwachung",
    "feature_4_desc": "Trupp- und Drucküberwachung mit lückenloser Erfassung der "
                      "Atemschutzträger.",
    "feature_5_title": "Personen & Patienten",
    "feature_5_desc": "Betroffene erfassen, Triage-Status und Transportkapazitäten "
                      "jederzeit im Blick.",
    "feature_6_title": "Einsatzchronik & PDF",
    "feature_6_desc": "Lückenlose, rechtssichere Protokollierung aller Schritte – auf Knopfdruck "
                      "als PDF exportierbar.",
    "about_title": "Über einsatzleiter.cloud",
    "about_text": "einsatzleiter.cloud ist ein digitales Hilfswerkzeug für die Einsatzleitung von "
                  "Feuerwehren und Rettungsdiensten. Es entstand aus der Praxis: aus dem Bedürfnis, "
                  "bei Einsätzen den Überblick zu behalten, Aufträge sauber zu koordinieren und alles "
                  "rechtssicher zu dokumentieren – ohne Zettelwirtschaft.\n\n"
                  "Das Werkzeug ist bewusst mobil gedacht, läuft im Einsatzleitwagen genauso wie am "
                  "Tablet vor Ort und synchronisiert alle Informationen in Echtzeit zwischen den "
                  "Beteiligten.",
    "contact_heading": "Kontakt aufnehmen",
    "contact_subtitle": "Fragen, Interesse oder Feedback? Schreiben Sie uns – wir melden uns zurück.",
    "impressum_betreiber": "Johannes Battlogg",
    "impressum_email": "johannes@battlogg.org",
    "impressum_address": "",
    "impressum_extra": "Idee: Roman Reiter\nUmsetzung: Johannes Battlogg",
}

# Reihenfolge & Beschriftung für das Admin-Formular: (key, label, multiline)
TEXT_FIELDS: list[tuple[str, str, bool]] = [
    ("hero_title", "Hero – Titel", False),
    ("hero_highlight", "Hero – hervorgehobener Teil", False),
    ("hero_subtitle", "Hero – Untertitel", True),
    ("features_heading", "Features – Überschrift", False),
    ("feature_1_title", "Feature 1 – Titel", False),
    ("feature_1_desc", "Feature 1 – Text", True),
    ("feature_2_title", "Feature 2 – Titel", False),
    ("feature_2_desc", "Feature 2 – Text", True),
    ("feature_3_title", "Feature 3 – Titel", False),
    ("feature_3_desc", "Feature 3 – Text", True),
    ("feature_4_title", "Feature 4 – Titel", False),
    ("feature_4_desc", "Feature 4 – Text", True),
    ("feature_5_title", "Feature 5 – Titel", False),
    ("feature_5_desc", "Feature 5 – Text", True),
    ("feature_6_title", "Feature 6 – Titel", False),
    ("feature_6_desc", "Feature 6 – Text", True),
    ("about_title", "About – Titel", False),
    ("about_text", "About – Text", True),
    ("contact_heading", "Kontakt – Überschrift", False),
    ("contact_subtitle", "Kontakt – Untertitel", True),
    ("impressum_betreiber", "Impressum – Betreiber", False),
    ("impressum_email", "Impressum – E-Mail", False),
    ("impressum_address", "Impressum – Adresse", True),
    ("impressum_extra", "Impressum – Zusatz (Idee/Umsetzung)", True),
]


def get_landing_content(db) -> dict:
    """Liefert Texte (Default + DB-Overrides) und Bild-URLs für die Templates."""
    content: dict = dict(TEXT_DEFAULTS)
    rows = db.query(SystemSettings).filter(
        SystemSettings.key.like(SETTINGS_PREFIX + "%")
    ).all()
    images_present: dict[str, bool] = {}
    for row in rows:
        if row.key.startswith(IMG_PREFIX):
            slug = row.key[len(IMG_PREFIX):]
            images_present[slug] = bool(row.value)
            continue
        short = row.key[len(SETTINGS_PREFIX):]
        if row.value:
            content[short] = row.value

    content["images"] = {
        slug: (f"/startseite/bild/{slug}" if images_present.get(slug) else None)
        for slug in IMAGE_SLUGS
    }
    content["year"] = datetime.now(UTC).year
    return content


def image_file_path(db, slug: str) -> Path | None:
    """Absoluter Pfad zur hinterlegten Bilddatei eines Slugs (oder None)."""
    if slug not in IMAGE_SLUGS:
        return None
    row = db.query(SystemSettings).filter_by(key=IMG_PREFIX + slug).first()
    if not row or not row.value:
        return None
    path = LANDING_DIR / row.value
    return path if path.exists() else None


def set_setting(db, key: str, value: str, user_id: int | None = None) -> None:
    """Upsert eines SystemSettings-Eintrags."""
    row = db.query(SystemSettings).filter_by(key=key).first()
    if row is None:
        row = SystemSettings(key=key)
        db.add(row)
    row.value = value
    row.updated_at = datetime.now(UTC)
    row.updated_by_user_id = user_id


def store_image(db, slug: str, filename: str, user_id: int | None = None) -> None:
    """Merkt sich den Dateinamen des hochgeladenen Bildes und löscht das alte."""
    old = db.query(SystemSettings).filter_by(key=IMG_PREFIX + slug).first()
    if old and old.value and old.value != filename:
        try:
            (LANDING_DIR / old.value).unlink(missing_ok=True)
        except OSError:
            logger.warning("Altes Startseiten-Bild konnte nicht gelöscht werden: %s", old.value)
    set_setting(db, IMG_PREFIX + slug, filename, user_id)
