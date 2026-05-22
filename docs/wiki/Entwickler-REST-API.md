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

**Felderer Überblick:**

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `Key` | string (UUID) | Eindeutiger Schlüssel für Idempotenz |
| `Nummer` | integer | Einsatznummer aus dem Alarmierungssystem |
| `AlarmDatumZeit` | ISO-8601 | Zeitpunkt des Alarms |
| `Stufe` | string | Alarmstufe (t1–t9, f1–f4) |
| `Art` | string | Einsatzart: `T` (Technik) oder `F` (Feuer) |
| `Meldung` | string | Freitext-Meldung |
| `Einsatzgrund` | string | Kurzer Grund |
| `Ort` | string | Ort/Gemeinde |
| `Strasse` | string | Straße |
| `HausNr` | string | Hausnummer |
| `Uebung` | boolean | Übungseinsatz? |

**Response (200 OK):**

```json
{
  "id": 42,
  "external_key": "426747e9-0126-45bc-a0c1-b51a182de14b",
  "url": "/einsatz/42",
  "created": true
}
```

Bei Idempotenz (Key bereits bekannt): `"created": false`, `"id": <vorhandene ID>`

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

Response: Array von Einsatz-Objekten mit `id`, `alarm_type_code`, `started_at`, `address_*`.

### GET /api/v1/einsatz/{id} — Einzelner Einsatz

```http
GET /api/v1/einsatz/42
X-API-Key: fwwo_...
```

Response: Vollständiges Einsatz-Objekt mit Fahrzeugen, Aufträgen, Status.

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

## curl-Beispiele

```bash
# Einsatz anlegen:
curl -X POST https://einsatzleiter.feuerwehr-wolfurt.at/api/v1/einsatz \
  -H "X-API-Key: fwwo_xxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "Key": "test-uuid-001",
    "Nummer": 100,
    "AlarmDatumZeit": "2026-05-22T14:30:00",
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
