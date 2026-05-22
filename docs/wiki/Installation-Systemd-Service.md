# Systemd-Service

← [Zurück zur Startseite](Home)

## Unit-Datei kopieren

```bash
sudo cp /home/clp-einsatz/htdocs/einsatzleiter/deploy/einsatzleiter.service \
        /etc/systemd/system/einsatzleiter.service
```

## Unit-Datei anpassen

```bash
sudo nano /etc/systemd/system/einsatzleiter.service
```

Relevante Zeilen:

```ini
[Service]
User=clp-einsatz
WorkingDirectory=/home/clp-einsatz/htdocs/einsatzleiter
EnvironmentFile=/home/clp-einsatz/htdocs/einsatzleiter/.env
ExecStart=/home/clp-einsatz/htdocs/einsatzleiter/.venv/bin/gunicorn \
    -k uvicorn.workers.UvicornWorker \
    -w 2 \
    --bind 127.0.0.1:8000 \
    app.main:app
```

> Passe `User` und `WorkingDirectory` an deinen tatsächlichen CloudPanel-Site-User an.

## Dienst aktivieren und starten

```bash
sudo systemctl daemon-reload
sudo systemctl enable einsatzleiter
sudo systemctl start einsatzleiter
sudo systemctl status einsatzleiter
```

Erwartete Ausgabe: `Active: active (running)`

## Logs anzeigen

```bash
# Aktuelle Logs:
journalctl -u einsatzleiter -f

# Letzte 100 Zeilen:
journalctl -u einsatzleiter -n 100

# Seit gestern:
journalctl -u einsatzleiter --since yesterday
```

## Dienst neu starten (z.B. nach Update)

```bash
sudo systemctl restart einsatzleiter
```

## Dienst stoppen

```bash
sudo systemctl stop einsatzleiter
```

## Anzahl Worker anpassen

Für 2 CPU-Kerne sind 2 Worker optimal. Formel: `2 × CPU-Kerne + 1`.  
Worker-Zahl in `/etc/systemd/system/einsatzleiter.service` anpassen → `daemon-reload` → `restart`.

> **Hinweis WebSockets:** Mit mehreren Workern muss ein Shared-State für WebSocket-Verbindungen vorhanden sein (Redis Pub/Sub). Bei einem einzelnen Server und 2 Workern funktioniert es ohne Redis, wenn NGINX alle WebSocket-Verbindungen an denselben Worker weiterleitet (Sticky Sessions via `ip_hash`). Einfachste Lösung für Einzelserver: `-w 1`.

---

**Nächster Schritt:** [NGINX Reverse-Proxy konfigurieren](Installation-NGINX-Reverse-Proxy)
