# Troubleshooting

← [Zurück zur Startseite](Home)

## App startet nicht

**Symptom:** `systemctl status einsatzleiter` zeigt `failed`

```bash
# Details anzeigen:
journalctl -u einsatzleiter -n 50 --no-pager
```

Häufige Ursachen:

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| `Can't connect to MySQL server` | DB-Verbindung schlägt fehl | DATABASE_URL in `.env` prüfen, MariaDB läuft? |
| `ImportError: No module named 'app'` | venv nicht aktiviert / falscher Pfad | `WorkingDirectory` in service-Datei prüfen |
| `Address already in use` | Port 8000 belegt | `ss -tlnp \| grep 8000` → Prozess beenden |
| `SECRET_KEY not set` | `.env` nicht geladen | `EnvironmentFile` in service-Datei prüfen |

## Login funktioniert nicht

- Passwort falsch → Reset: `python -m app.cli reset-password --username admin --password neues-pw`
- Session-Cookie blockiert → Browser-Cache leeren, HTTPS prüfen (Cookies werden nur über HTTPS gesetzt)
- `.env` SECRET_KEY geändert → alle Sessions werden ungültig, neu einloggen

## WebSocket-Verbindung bricht ab

```bash
# NGINX-Logs prüfen:
tail -f /var/log/nginx/error.log
```

Häufige Ursachen:
- **Upgrade-Header fehlt:** NGINX-Konfiguration um `proxy_set_header Upgrade $http_upgrade;` ergänzen
- **Timeout:** `proxy_read_timeout 3600s;` setzen
- **Mehrere Worker:** Sticky Sessions via `ip_hash` in NGINX upstream aktivieren

## PDF-Generierung schlägt fehl

```bash
journalctl -u einsatzleiter | grep -i weasyprint
```

Häufige Ursachen:
- Fehlende Systempakete: `sudo apt-get install -y libpango-1.0-0 libpangoft2-1.0-0`
- Schriftarten fehlen: `sudo apt-get install -y fonts-liberation`

## API-Key wird abgelehnt (401)

1. Key existiert: `python -m app.cli list-api-keys`
2. Key nicht widerrufen: Spalte `revoked_at` ist NULL?
3. Key nicht abgelaufen: Spalte `expires_at` ist NULL oder in der Zukunft?
4. Header korrekt: `X-API-Key: fwwo_xxxx` (nicht `Bearer fwwo_xxxx`)

## Alembic-Migration schlägt fehl

```bash
alembic current
alembic history
```

Falls die Datenbank in einem inkonsistenten Zustand ist:
```bash
# Aktuellen Stand erzwingen (Vorsicht!):
alembic stamp head
```

## Push-Benachrichtigungen werden nicht zugestellt

1. VAPID-Keys in `.env` korrekt gesetzt?
2. `APP_BASE_URL` korrekt (wird als VAPID-Subject verwendet)?
3. Browser hat Permission erteilt?
4. Logs: `journalctl -u einsatzleiter | grep -i push`

## Hoher Speicherverbrauch

WeasyPrint kann für große PDFs viel RAM brauchen. Falls der Server unter Last gerät:
- Anzahl Gunicorn-Worker reduzieren (`-w 1`)
- PDF-Generierung in einen separaten Queue-Worker auslagern (zukünftiges Feature)

## Port 8000 von außen erreichbar

Firewall-Regel hinzufügen:
```bash
sudo ufw deny 8000/tcp
```

Nur NGINX (80/443) soll von außen erreichbar sein.
