# REST-API

← [Zurück zur Startseite](Home)

Die REST-API ist für **externe Systeme** (Alarmierungssystem) gedacht. Alle Endpunkte erfordern einen gültigen API-Key.

## Authentifizierung

```http
X-API-Key: fwwo_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Endpunkte

### POST /api/v1/einsatz — Einsatz anlegen

Legt einen neuen Einsatz an (oder gibt den bestehenden zurück bei Idempotenz).

**Request:**

```http
POST /api/v1/einsatz
X-API-Key: fwwo_...
Content-Type: application/json
```

```json
{
  "Key": "426747e9-0126-45bc-a0c1-b51a182de14b",
  "Nummer": 1978,
  "AlarmDatumZeit": "2026-05-19T21:11:11.323",
  "Zeitzone": "Europe/Vienna",
  "Stufe": "t9",
  "Art": "T",
  "Meldung": "wolfurt senderstraße 34 heizraum überflutet",
  "Einsatzgrund": "heizraum überflutet",
  "Ort": "Wolfurt",
  "Strasse": "Senderstraße",
  "HausNr": "34",
  "Uebung": false
}
```

**Felder Überblick:**

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `Key` | string | ja | Eindeutiger Schlüssel für Idempotenz |
| `Nummer` | integer | nein | Einsatznummer aus dem Alarmierungssystem |
| `AlarmDatumZeit` | ISO-8601 | nein | Zeitpunkt des Alarms (mit oder ohne UTC-Offset) |
| `Zeitzone` | string (IANA) | nein | Zeitzone für naive `AlarmDatumZeit` — siehe unten |
| `Stufe` | string | nein | Alarmstufe (t1–t9, f1–f4) |
| `Art` | string | nein | Einsatzart: `T` (Technik) oder `F` (Feuer) |
| `Meldung` | string | nein | Freitext-Meldung |
| `Einsatzgrund` | string | nein | Kurzer Grund |
| `Ort` | string | nein | Ort/Gemeinde |
| `Strasse` | string | nein | Straße |
| `HausNr` | string | nein | Hausnummer |
| `Uebung` | boolean | nein | Übungseinsatz? (Standard: `false`) |

#### Zeitzone-Handling

`AlarmDatumZeit` kann auf zwei Arten übergeben werden:

- **Mit UTC-Offset** (empfohlen): `"2026-05-19T21:11:11+02:00"` — wird direkt übernommen.
- **Naiv (ohne Offset)**: `"2026-05-19T21:11:11.323"` — der Server interpretiert die Zeit in der Zeitzone, die durch folgende Priorität bestimmt wird:
  1. `Zeitzone`-Feld im Request (z. B. `"Europe/Vienna"`)
  2. In der Organisation hinterlegte Zeitzone
  3. Server-Default (`Europe/Vienna`)

Intern werden alle Zeitpunkte als UTC gespeichert.

**Response (200 OK):**

```json
{
  "id": 42,
  "external_key": "426747e9-0126-45bc-a0c1-b51a182de14b",
  "url": "/einsatz/42",
  "created": true,
  "board_token": "InVzZXJfaWQiOiAxfQ.abc123...",
  "board_url": "https://einsatzleiter.example.at/qr-login?incident_id=42&token=InVzZXJfaWQiOiAxfQ.abc123..."
}
```

Bei Idempotenz (Key bereits bekannt): `"created": false`, `"id": <vorhandene ID>` — `board_token` und `board_url` werden ebenfalls zurückgegeben.

**Response-Felder:**

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `id` | integer | Interne Einsatz-ID |
| `external_key` | string | Mitgegebener Idempotenz-Schlüssel |
| `url` | string | Relativer Pfad zum Einsatz-Board |
| `created` | boolean | `true` bei Neuanlage, `false` bei Idempotenz-Treffer |
| `board_token` | string\|null | Signiertes QR-Token für direkten Board-Zugriff — siehe unten |
| `board_url` | string\|null | Vollständige Login-URL für QR-Code-Zugriff auf das Board |

#### Board-Token / QR-Code-Zugriff

`board_token` und `board_url` ermöglichen passwortlosen Direktzugriff auf das Einsatz-Board, solange der Einsatz aktiv ist — dasselbe Verfahren, das auch der QR-Code in der Benutzeroberfläche nutzt.

**Verwendung:**
- `board_url` direkt als QR-Code rendern oder in Benachrichtigungen verlinken
- Öffnen der URL in einem Browser meldet den verknüpften Benutzer automatisch an und leitet auf das Board weiter
- Token ist an den Benutzer gebunden, der den API-Key erstellt hat
- Gültigkeit endet automatisch, wenn der Einsatz geschlossen oder archiviert wird

`board_token` und `board_url` sind `null`, wenn dem API-Key kein Benutzer zugeordnet ist (Legacy-Keys).

**Fehler-Responses:**

| Code | Bedeutung |
|------|-----------|
| 401 | API-Key ungültig oder fehlt |
| 422 | Payload-Validierungsfehler |
| 500 | Serverfehler |

### GET /api/v1/einsatz/active — Aktive Einsätze

```http
GET /api/v1/einsatz/active
X-API-Key: fwwo_...
```

Response: Array von Einsatz-Objekten mit `id`, `alarm_type_code`, `started_at`, `is_exercise`.

### GET /api/v1/einsatz/{id} — Einzelner Einsatz

```http
GET /api/v1/einsatz/42
X-API-Key: fwwo_...
```

Response: Vollständiges Einsatz-Objekt mit `id`, `alarm_type_code`, `status`, `started_at`, `address`, `is_exercise`.

## Stufen-Mapping

| Payload-Stufe | Intern | Bedeutung |
|---------------|--------|-----------|
| `t1` | T1 | Techn. Hilfe klein |
| `t2` | T2 | Techn. Hilfe mittel |
| `t3` | T3 | Techn. Hilfe groß |
| `t6` | T6 | Massenanfall |
| `t9` | T3 | Unbekannte Stufe → T3 Fallback |
| `f1` | F1 | Brand klein |
| `f2` | F2 | Brand mittel |
| `f3` | F3 | Brand groß |
| `f4` | F4 | Großbrand |
| `f14` | F14 | Großbrand Sonderstufe |

## curl-Beispiele

```bash
# Einsatz anlegen mit expliziter Zeitzone:
curl -X POST https://einsatzleiter.feuerwehr-wolfurt.at/api/v1/einsatz \
  -H "X-API-Key: fwwo_xxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "Key": "test-uuid-001",
    "Nummer": 100,
    "AlarmDatumZeit": "2026-05-22T14:30:00",
    "Zeitzone": "Europe/Vienna",
    "Stufe": "t1",
    "Art": "T",
    "Meldung": "Wasserschaden Keller",
    "Einsatzgrund": "Wasserschaden",
    "Ort": "Wolfurt",
    "Strasse": "Teststraße",
    "HausNr": "1",
    "Uebung": false
  }'

# Aktive Einsätze:
curl https://einsatzleiter.feuerwehr-wolfurt.at/api/v1/einsatz/active \
  -H "X-API-Key: fwwo_xxxx"
```
