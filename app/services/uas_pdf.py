"""PDF-Export für UAS-Formulare via WeasyPrint (ÖBFV Anh. 8.1–8.5, RL-UAS LFV Vbg. Jan 2024)."""
from __future__ import annotations

import io
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.uas import UASCheckliste, UASEreignis, UASFlug, UASPilot, UASWartung

_CSS_BASE = """
@page { margin: 1.5cm; font-size: 11pt; }
body { font-family: Arial, sans-serif; color: #111; }
h1 { font-size: 14pt; border-bottom: 2px solid #111; padding-bottom: 4px; margin-bottom: 8px; }
h2 { font-size: 12pt; margin: 12px 0 4px; }
table { width: 100%; border-collapse: collapse; margin-bottom: 8px; }
th { background: #e8e8e8; text-align: left; padding: 4px 6px; font-size: 10pt; }
td { padding: 4px 6px; border-bottom: 1px solid #ccc; font-size: 10pt; }
.label { font-weight: bold; width: 38%; }
.check { font-size: 10pt; }
.check-ok  { color: #166534; }
.check-nok { color: #991b1b; }
.footer { font-size: 8pt; color: #666; margin-top: 12px; }
"""


def _render_pdf(html: str) -> bytes:
    from weasyprint import CSS, HTML  # lazy import – optional dependency
    buf = io.BytesIO()
    HTML(string=html).write_pdf(buf, stylesheets=[CSS(string=_CSS_BASE)])
    return buf.getvalue()


# ── Anh. 8.1: Flugbuch-Seite ─────────────────────────────────────────────────

def flugbuch_pdf(flug, pilot=None, device=None) -> bytes:
    rows = [
        ("Datum", str(flug.datum or "")),
        ("Pilot", pilot.vorname + " " + pilot.nachname if pilot else "–"),
        ("Gerät", device.bezeichnung if device else "–"),
        ("Durchführung", flug.durchfuehrung or "–"),
        ("Grundlage", flug.grundlage or "–"),
        ("Bescheid-Nr.", flug.bescheid_nr or "–"),
        ("Höhe (m)", str(flug.geplante_flughoehe_m or "–")),
        ("Cont. Vol. (m)", str(flug.contingency_volume_m or "–")),
        ("GRB (m)", str(flug.ground_risk_buffer_m or "–")),
        ("Abstand (m)", str(flug.abstand_menschenansammlung_m or "–")),
        ("1:1-Regel konform", "Ja" if flug.flughoehe_konform else "Nein"),
        ("Nachtbetrieb", "Ja" if flug.nachtbetrieb else "Nein"),
        ("Dauer (min)", str(flug.dauer_min or "–")),
        ("Status", flug.status or "–"),
    ]
    body = "\n".join(
        f'<tr><td class="label">{k}</td><td>{v}</td></tr>' for k, v in rows
    )
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>
<h1>UAS-Flugbuch – Flug #{flug.id} (Anh. 8.1)</h1>
<table><tbody>{body}</tbody></table>
<p class="footer">Erstellt gem. RL-UAS LFV Vorarlberg Jan 2024 | Formular Anh. 8.1</p>
</body></html>"""
    return _render_pdf(html)


# ── Anh. 8.2: Checkliste Vor-/Nachflug ───────────────────────────────────────

def checkliste_pdf(checkliste, flug_id: int | None = None) -> bytes:
    punkte = checkliste.punkte if isinstance(checkliste.punkte, list) else []
    rows = ""
    for p in punkte:
        ok = "&#x2713;" if p.get("erledigt") else "&#x2717;"
        css = "check-ok" if p.get("erledigt") else "check-nok"
        rows += f'<tr><td class="check {css}">{ok}</td><td>{p.get("text","")}</td></tr>'
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>
<h1>Checkliste {checkliste.typ} – Flug #{flug_id} (Anh. 8.2)</h1>
<table><thead><tr><th width="30"></th><th>Prüfpunkt</th></tr></thead>
<tbody>{rows}</tbody></table>
<p>Erledigt von (Pilot): {checkliste.erledigt_von_pilot or "–"}<br>
   Zweitperson: {checkliste.erledigt_von_zweitperson or "–"}<br>
   Abgeschlossen: {checkliste.abgeschlossen_at or "–"}</p>
<p class="footer">Erstellt gem. RL-UAS LFV Vorarlberg Jan 2024 | Formular Anh. 8.2</p>
</body></html>"""
    return _render_pdf(html)


# ── Anh. 8.3: Notfallprotokoll / Ereignisbericht ─────────────────────────────

def ereignis_pdf(ereignis) -> bytes:
    rows = [
        ("Typ", ereignis.typ or "–"),
        ("Kategorie", ereignis.kategorie or "–"),
        ("Datum lokal", str(ereignis.datum_lokal or "–")),
        ("Uhrzeit lokal", ereignis.zeit_lokal or "–"),
        ("Datum UTC", str(ereignis.datum_utc or "–")),
        ("Uhrzeit UTC", ereignis.zeit_utc or "–"),
        ("Ort (ICAO)", ereignis.ort_icao or "–"),
        ("Klassifizierung", ereignis.klassifizierung or "–"),
    ]
    body = "\n".join(
        f'<tr><td class="label">{k}</td><td>{v}</td></tr>' for k, v in rows
    )
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>
<h1>Notfall-/Unfallprotokoll #{ereignis.id} (Anh. 8.3)</h1>
<table><tbody>{body}</tbody></table>
<h2>Hergang / Beschreibung</h2>
<p style="white-space:pre-wrap">{ereignis.beschreibung or "–"}</p>
<h2>Getroffene Maßnahmen</h2>
<p>{ereignis.massnahmen or "–"}</p>
<p class="footer">Erstellt gem. RL-UAS LFV Vorarlberg Jan 2024 | Formular Anh. 8.3</p>
</body></html>"""
    return _render_pdf(html)


# ── Anh. 8.4: ACG Unfall-Meldung ─────────────────────────────────────────────

def acg_unfall_pdf(ereignis) -> bytes:
    rows = [
        ("Datum lokal", str(ereignis.datum_lokal or "–")),
        ("Zeit lokal", ereignis.zeit_lokal or "–"),
        ("Datum UTC", str(ereignis.datum_utc or "–")),
        ("Zeit UTC", ereignis.zeit_utc or "–"),
        ("Ort (ICAO)", ereignis.ort_icao or "–"),
        ("Koordinaten", ereignis.koordinaten or "–"),
        ("Klassifizierung", ereignis.klassifizierung or "–"),
    ]
    body = "\n".join(
        f'<tr><td class="label">{k}</td><td>{v}</td></tr>' for k, v in rows
    )
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>
<h1>ACG Unfall-Meldung – Ereignis #{ereignis.id} (Anh. 8.4)</h1>
<table><tbody>{body}</tbody></table>
<h2>Beschreibung des Ereignisses</h2>
<p style="white-space:pre-wrap">{ereignis.beschreibung or "–"}</p>
<p class="footer">Erstellt gem. RL-UAS LFV Vorarlberg Jan 2024 | Formular Anh. 8.4<br>
An ACG (Austro Control GmbH) zu melden gem. Luftfahrtgesetz §147a.</p>
</body></html>"""
    return _render_pdf(html)


# ── Anh. 8.5: Wartungsbuch ───────────────────────────────────────────────────

def wartungsbuch_pdf(wartungen: list, device=None) -> bytes:
    rows = ""
    for w in wartungen:
        rows += (
            f"<tr><td>{w.faellig_am or '–'}</td><td>{w.typ or '–'}</td>"
            f"<td>{w.durchgefuehrt_am or '–'}</td><td>{w.ergebnis or '–'}</td>"
            f"<td>{w.techniker or '–'}</td></tr>"
        )
    if not rows:
        rows = '<tr><td colspan="5" style="text-align:center">Keine Einträge</td></tr>'
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>
<h1>Wartungsbuch – {device.bezeichnung if device else "Gerät"} (Anh. 8.5)</h1>
<table>
<thead><tr><th>Fällig am</th><th>Typ</th><th>Durchgef.</th><th>Ergebnis</th><th>Techniker</th></tr></thead>
<tbody>{rows}</tbody>
</table>
<p class="footer">Erstellt gem. RL-UAS LFV Vorarlberg Jan 2024 | Formular Anh. 8.5</p>
</body></html>"""
    return _render_pdf(html)


# ── Anh. 8.6: Eintreffmeldung / Pilotenausweis ───────────────────────────────

def eintreffmeldung_pdf(einsatz, piloten: list) -> bytes:
    rows = ""
    for p in piloten:
        rows += (
            f"<tr><td>{p.vorname} {p.nachname}</td><td>{p.bos_ausweisnummer or '–'}</td>"
            f"<td>{p.zertifikat_a2 or '–'}</td></tr>"
        )
    if not rows:
        rows = '<tr><td colspan="3" style="text-align:center">Keine Piloten</td></tr>'
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>
<h1>Eintreffmeldung UAS-Einheit (Anh. 8.6)</h1>
<table><tbody>
<tr><td class="label">Einsatz-ID</td><td>#{einsatz.id}</td></tr>
<tr><td class="label">Status</td><td>{einsatz.status or "–"}</td></tr>
<tr><td class="label">Betreiber-Nr.</td><td>{einsatz.betreibernummer or "–"}</td></tr>
<tr><td class="label">TETRA-Rufname</td><td>{einsatz.tetra_rufname or "–"}</td></tr>
<tr><td class="label">Gesamteinsatzleiter</td><td>{einsatz.gesamteinsatzleiter or "–"}</td></tr>
</tbody></table>
<h2>Eingesetzte Piloten</h2>
<table>
<thead><tr><th>Name</th><th>BOS-Ausweis</th><th>A2-Zertifikat</th></tr></thead>
<tbody>{rows}</tbody>
</table>
<p class="footer">Erstellt gem. RL-UAS LFV Vorarlberg Jan 2024 | Formular Anh. 8.6</p>
</body></html>"""
    return _render_pdf(html)
