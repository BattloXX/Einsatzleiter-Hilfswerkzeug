# Benutzer und Rollen

← [Zurück zur Startseite](Home)

## Benutzer verwalten

**Admin** → **Benutzer**

### Neuen Benutzer anlegen

**+ Neuer Benutzer** → Formular:

| Feld | Beschreibung |
|------|-------------|
| Benutzername | Eindeutig, für Login (z.B. `stefan.m`) |
| Anzeigename | Wird im Board und PDF angezeigt |
| Passwort | Min. 8 Zeichen |
| Aktiv | Deaktivierte Benutzer können sich nicht einloggen |

Nach Anlage: Rollen zuweisen (siehe unten).

### Passwort zurücksetzen

Benutzer in der Liste → **Passwort zurücksetzen** → neues Passwort eingeben → **Speichern**

Oder per CLI (für Admin-Passwort ohne Login):
```bash
python -m app.cli reset-password --username admin --password neues-passwort
```

### Benutzer deaktivieren

Benutzer in der Liste → **Deaktivieren** → Bestätigen.  
Der Benutzer kann sich nicht mehr einloggen. Alle historischen Einträge (Audit-Log, Einsätze) bleiben ihm zugeordnet.

## Rollen

### Rollenbeschreibung

| Rolle | Code | Beschreibung |
|-------|------|-------------|
| **System-Administrator** | `system_admin` | Zugriff auf alle Organisationen, System-Konsole |
| **Organisations-Administrator** | `org_admin` | Eigene Org verwalten (Einstellungen, Mitglieder, Fahrzeuge) |
| **Administrator** | `admin` | Vollzugriff innerhalb der eigenen Org |
| **Einsatzleiter** | `incident_leader` | Einsatz und Atemschutz steuern |
| **AS-Überwacher** | `breathing_supervisor` | Nur Atemschutzüberwachung |
| **Schriftführer** | `recorder` | Journal-Einträge und Meldungen |
| **Beobachter** | `readonly` | Nur lesend |

`system_admin` und `org_admin` sind Multi-Tenancy-Rollen (ab v2.2.0). Der erste Admin-User der Heimwehr erhält automatisch `org_admin`.

### Berechtigungsmatrix

| Aktion | system_admin | org_admin / admin | incident_leader | breathing_supervisor | recorder | readonly |
|--------|:------------:|:-----------------:|:---------------:|:--------------------:|:--------:|:--------:|
| Einsatz anlegen (manuell) | ✓ | ✓ | ✓ | – | – | – |
| Fahrzeuge verschieben | ✓ | ✓ | ✓ | – | – | – |
| Aufträge anlegen/bearbeiten | ✓ | ✓ | ✓ | – | – | – |
| Meldungen anlegen | ✓ | ✓ | ✓ | – | ✓ | – |
| Personen erfassen | ✓ | ✓ | ✓ | – | ✓ | – |
| Atemschutz steuern | ✓ | ✓ | ✓ | ✓ | – | – |
| Einsatz abschließen | ✓ | ✓ | ✓ | – | – | – |
| PDF herunterladen | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Stammdaten pflegen | ✓ | ✓ | – | – | – | – |
| Benutzer verwalten | ✓ | ✓ | – | – | – | – |
| API-Keys verwalten | ✓ | ✓ | – | – | – | – |
| Audit-Log einsehen | ✓ | ✓ | – | – | – | – |
| Organisationen verwalten | ✓ | – | – | – | – | – |
| System-Konsole | ✓ | – | – | – | – | – |

### Rollen zuweisen

Benutzer in der Liste → **Rollen** → gewünschte Rollen aktivieren → **Speichern**

Ein Benutzer kann mehrere Rollen haben (z.B. `incident_leader` + `breathing_supervisor`).

## Hinweise

- Der erste Admin-User wird automatisch beim App-Start aus `.env` (`BOOTSTRAP_ADMIN_*`) angelegt und erhält die Rollen `admin` und `org_admin`.
- Mindestens ein aktiver Admin-User muss immer vorhanden sein.
- Die Anzahl der Benutzer ist nicht begrenzt.
- Benutzer ohne `org_id` (NULL) sind System-Administratoren und sehen alle Organisationen.
- `org_admin` kann Einladungen an neue Org-Admins versenden: [Organisationen verwalten](Administration-Organisations-verwalten).
