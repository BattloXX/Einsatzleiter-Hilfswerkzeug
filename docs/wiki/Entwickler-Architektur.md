# Architektur

← [Zurück zur Startseite](Home)

## Schichten-Übersicht

```
Browser (HTMX + Alpine.js + WebSocket)
         │ HTTP/2 + WSS
    NGINX (Reverse Proxy, TLS, Static Files)
         │ HTTP/1.1 (127.0.0.1:8000)
    Gunicorn + UvicornWorker (2 Worker)
         │
    FastAPI (app/main.py)
    ├── Routers (HTTP-Endpunkte)
    │   ├── auth.py       – Login/Logout/QR-Login
    │   ├── ui_incident.py – Einsatz-Board (HTMX-Partials)
    │   ├── ui_breathing.py – AS-Überwachung
    │   ├── ui_admin.py   – Admin-UI
    │   ├── ui_archive.py – Archiv & PDF
    │   ├── ui_stats.py   – Statistik
    │   ├── ui_push.py    – Push-Subscribe
    │   ├── api_v1.py     – REST-API (extern)
    │   └── ws.py         – WebSocket-Endpoint
    ├── Services (Geschäftslogik)
    │   ├── incident_service.py
    │   ├── breathing_service.py
    │   ├── broadcast.py   – WS Pub/Sub
    │   ├── pdf_service.py – WeasyPrint
    │   └── push_service.py – VAPID Push
    ├── Models (SQLAlchemy ORM)
    │   ├── user.py, master.py, incident.py, breathing.py
    └── Core
        ├── security.py   – Passwort, Session, API-Key, QR
        ├── permissions.py – Rollen-Checks
        └── audit.py      – Audit-Log-Writer
         │
    SQLAlchemy 2.x (ORM + Alembic Migrations)
         │
    MariaDB 10.11 (UTF8MB4, InnoDB)
```

## Realtime-Architektur (WebSockets)

```
Browser A ──WS──┐
Browser B ──WS──┤── ConnectionManager ── broadcast(incident_id, event)
Browser C ──WS──┘         │
                         Pub/Sub Dict[int, Set[WebSocket]]
                         Channel 0 = Global (neue Einsätze)
                         Channel N = Einsatz N
```

Bei jeder schreibenden Aktion:
1. Datenbank-Schreiboperation (in Transaction)
2. `IncidentChange`-Eintrag schreiben
3. Nach Commit: `broadcast.publish(incident_id, event)` mit HTML-Partial
4. Alle verbundenen Clients patchen ihr DOM (`htmx.swap`)

## Request-Lifecycle (typisch)

```
1. Browser sendet HTMX-POST (z.B. Auftrag erledigen)
2. FastAPI-Router validiert Session-Cookie → User
3. require_role()-Dependency prüft Berechtigung
4. Service-Funktion führt DB-Änderung durch
5. audit.write_incident_change() schreibt Change-Log
6. DB-Commit
7. broadcast.publish() → alle WS-Clients erhalten Event
8. Router gibt HTML-Partial zurück (HTMX-Swap)
9. Audit: push_service.send() falls relevantes Event
```

## Frontend-Technologien

| Technologie | Rolle |
|-------------|-------|
| **HTMX** | Server-rendered Partial-Updates (kein SPA) |
| **Alpine.js** | Reaktivität für Toasts, Timer, WS-Handler |
| **SortableJS** | Drag&Drop → HTMX-POST |
| **Web Speech API** | Sprachdiktat (Browser-nativ) |
| **Service Worker** | PWA, Offline-Cache |
| **Web Push API** | Push-Benachrichtigungen (VAPID) |

## Datenfluss bei WebSocket-Event

```
1. Server-Event: broadcast.publish(42, {"type": "task_done", "partial_html": "<div>..."})
2. WS-Client (app.js) empfängt JSON
3. Alpine/HTMX swappt das Partial ins DOM
4. Falls type == 'alarm_popup': Modal wird angezeigt
5. Falls type == 'new_incident': Toast erscheint
```
