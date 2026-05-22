# Stammdaten pflegen

← [Zurück zur Startseite](Home)

Stammdaten sind die Grundkonfiguration der App: Fahrzeuge, Wehren, Alarmstichwörter, Auftragsvorschläge und Lage-Hinweise.

Sie werden beim ersten Start automatisch aus `app/seed_data.py` befüllt.

## Fahrzeuge

**Admin** → **Fahrzeuge**

### Fahrzeuge der eigenen Wehr

| Feld | Beschreibung |
|------|-------------|
| Code | Kürzel (z.B. `RLF`, `KDOF`) |
| Name | Vollständiger Name |
| Typ | Kategorisierung |
| Erstausrückung | ✓ = dieses Fahrzeug rückt bei T1/T2/F1/F2 aus |
| Reihenfolge | Sortierung im Board |
| Aktiv | Inaktive Fahrzeuge erscheinen nicht mehr |

### Nachbarwehren und deren Fahrzeuge

Unter **Wehren** können die Nachbarwehren mit ihren Fahrzeugen gepflegt werden.

Jede Wehr hat:
- **Slug**: Eindeutige Kennung (z.B. `lauterach`)
- **Name**: Anzeigename
- **Farbe**: Hex-Farbcode für den seitlichen Streifen auf den Karten

Voreingestellte Org-Farben:
| Wehr | Farbe |
|------|-------|
| Wolfurt | `#b71921` (Rot) |
| Lauterach | `#1877f2` (Blau) |
| Schwarzach | `#8e44ad` (Lila) |
| Bildstein | `#2e9d55` (Grün) |
| Bregenz | `#e67e22` (Orange) |
| Kennelbach | `#00a6a6` (Türkis) |

## Alarm-Stichwörter

**Admin** → **Stichwörter**

Jedes Stichwort hat:
- **Code**: z.B. `T1`, `F3`
- **Kategorie**: `Technik` oder `Feuer`
- **Erstausrückung**: Nur Erstausrückungsfahrzeuge oder alle?
- **Nachbarn**: Werden Nachbarwehren automatisch eingeblendet?

## Auftragsvorschläge

**Admin** → **Auftragsvorschläge**

Beim Einsatzstart werden für das gewählte Stichwort automatisch Auftragsvorschläge in der Sidebar angezeigt. Hier können diese gepflegt werden.

Vorschläge sind sortiert nach Reihenfolge-Zahl und werden nach Stichwort gefiltert.

## Lage-Hinweise

**Admin** → **Lage-Hinweise**

Rotierender Ticker in der Sidebar während eines Einsatzes. Kurze Erinnerungen an wichtige Maßnahmen:
- „Geräteträger auf Fremdgase achten"
- „Einsatzleitung dokumentieren"

## Atemschutz-Parameter

**Admin** → **Wehr-Einstellungen**

Die Rückzugsdruck-Formel ist parametrisierbar:

| Parameter | Standard | Beschreibung |
|-----------|---------|-------------|
| Faktor | 0,5 | Multiplikator für den Anfangsdruck |
| Reserve | 10 bar | Fixer Sicherheitszuschlag |

Formel: `Rückzugsdruck = Anfangsdruck × Faktor + Reserve`

> Standard nach FF Vorarlberg: 300 bar × 0,5 + 10 = **160 bar**

## Seed-Daten zurücksetzen

Falls die Stammdaten versehentlich gelöscht wurden:

```bash
python -m app.seed_data
```

> Achtung: Bestehende Daten werden nicht überschrieben, nur fehlende ergänzt.
