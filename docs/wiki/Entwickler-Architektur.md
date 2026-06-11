# Architektur

← [Zurück zur Startseite](Home)

## Schichten-Übersicht

```
Browser (HTMX + Alpine.js + WebSocket)
         │ HTTP/2 + WSS
    NGINX (Reverse Proxy, TLS, Static Files)
         │ HTTP/1.1 (127.0.0.1:8092)
    Gunicorn + UvicornWorker (2 Worker)
         │
    FastAPI (app/main.py)
    ├── Middleware-Stack
    │   ├── SessionMiddleware   – Cookie → request.state.user (Sliding Window)
    │   ├── SecurityHeadersMiddleware – CSP, X-Frame-Options, ...
    │   ├── CSRFMiddleware      – Double-Submit-Cookie-Pattern
    │   └── SlowAPI             – Rate-Limiting (IP + API-Key)
    ├── Routers (HTTP-Endpunkte)
    │   ├── auth.py             – Login / Logout / QR-Login / Geräte-Login
    │   ├── ui_incident.py      – Einsatz-Board (HTMX-Partials)
    │   ├── ui_breathing.py     – Atemschutzüberwachung
    │   ├── ui_media.py         – Galerie, Auth-geschützte Datei-Auslieferung
    │   ├── ui_archive.py       – Archiv & PDF-Export
    │   ├── ui_admin.py         – Stammdaten, Benutzer, API-Keys, Audit
    │   ├── ui_settings.py      – Org-Einstellungen, ZIP-Update
    │   ├── ui_backup.py        – Konfig-Export/Import (JSON, Dry-Run)
    │   ├── ui_sysadmin.py      – System-Admin-Konsole (per-Org KPIs)
    │   ├── ui_invitation.py    – Einladungslinks für neue Org-Admins
    │   ├── ui_ai_prompts.py    – KI-Prompt-Verwaltung (Versionierung)
    │   ├── ui_stats.py         – Statistik-Dashboard
    │   ├── ui_push.py          – Web-Push-Verwaltung
    │   ├── ui_password_reset.py
    │   ├── api_v1.py           – REST-API (Alarmierung, Lage-Alarm)
    │   ├── lagekarte_api.py    – GeoJSON-Feed für lagekarte.info
    │   └── ws.py               – WebSocket Pub/Sub
    ├── Core
    │   ├── security.py        – Passwort-Hashing, Session, API-Key, QR-Token
    │   ├── permissions.py     – require_role(), has_role(), can_access_incident()
    │   ├── queries.py         – visible_incidents_q() — Tenant-Filterung
    │   ├── rate_limit.py      – slowapi-Instanz + get_api_key_identifier()
    │   ├── audit.py           – Audit-Log-Writer
    │   └── templating.py      – Jinja2-Env + local-Filter
    ├── Services (Geschäftslogik)
    │   ├── incident_service.py
    │   ├── media_service.py   – Upload-Pipeline (Bild/PDF/Video/HEIC)
    │   ├── broadcast.py       – WS Pub/Sub-Manager
    │   ├── pdf_service.py     – WeasyPrint
    │   ├── push_service.py    – VAPID Push
    │   ├── autoclose.py       – Hintergrund-Job Auto-Schließen
    │   ├── ai_service.py      – Anthropic Claude
    │   ├── alarm_service.py   – Alarmtyp-Lookup
    │   ├── seed_service.py    – Seed-Template bei Org-Anlage
    │   ├── sms_service.py     – SMS via Gateway-Container
    │   ├── mail_service.py    – SMTP (Passwort-Reset, Einladungen)
    │   └── update_service.py  – ZIP-Update + Alembic
    └── Models (SQLAlchemy ORM)
        ├── incident.py   – Incident, Task, TaskMedia, IncidentOrg, IncidentToken, ...
        ├── user.py       – User, Role, ApiKey, AuditLog, DeviceToken, ...
        ├── master.py     – FireDept, Member (TenantScoped), AlarmType (TenantScoped), OrgSettings, SeedTemplate, ...
        ├── invitation.py – OrgInvitation
        └── breathing.py  – BreathingTroop, TroopMember, PressureLog
         │
    SQLAlchemy 2.x (ORM + do_orm_execute Tenant-Filter + Alembic)
         │
    MariaDB 10.11 (UTF8MB4, InnoDB, 55 Migrationen)
```

## Multi-Tenancy: Row-Level-Isolation

```
User (org_id=3) → Session-Cookie → SessionMiddleware → request.state.user
         │
    set_tenant_context(db, org_id=3)   ← bei jedem Request gesetzt
         │
    do_orm_execute Event (SQLAlchemy)
         └── db.query(TenantScoped) → automatisch WHERE org_id=3
                  │
    Modelle: Member, AlarmType, TaskSuggestion, MessageSuggestion,
             LageHint, DefaultMessage, AIPromptVersion

    AUSNAHME: db.get(Model, id)  ← umgeht den Event-Handler!
    → Router prüfen danach manuell: same_org_or_system_admin()
```

### Einsatz-Sichtbarkeit

```python
# app/core/queries.py
def visible_incidents_q(db, user):
    """Eigene Org (primary_org_id) + kollaborierende Orgs (IncidentOrg)."""
    if is_system_admin:  return db.query(Incident)          # alles
    if not user.org_id:  return db.query(Incident).filter(False)
    return db.query(Incident).filter(
        or_(Incident.primary_org_id == user.org_id,
            Incident.id.in_(collab_subquery))
    )
```

Verwendet in: `ui_incident.py` (Dashboard, Board), `ui_admin.py` (Admin-Dashboard), `api_v1.py`.

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
2. CSRF-Middleware prüft Double-Submit-Token
3. SessionMiddleware: Cookie → User aus DB → request.state.user
4. set_tenant_context(db, user.org_id) — Tenant-Filter aktivieren
5. require_role()-Dependency prüft Berechtigung
6. Service-Funktion führt DB-Änderung durch
7. audit.write_incident_change() schreibt Change-Log
8. DB-Commit
9. broadcast.publish() → alle WS-Clients erhalten Event
10. Router gibt HTML-Partial zurück (HTMX-Swap)
```

## Rate-Limiting

```
POST /login              → IP-basiert (LOGIN_RATELIMIT, Standard: 10/min)
POST /api/v1/einsatz     → API-Key-basiert (API_ALARM_RATELIMIT, Standard: 60/min)
POST /api/v1/lage/alarm  → API-Key-basiert
Medien-Upload            → IP-basiert (UPLOAD_RATELIMIT, Standard: 20/min)
Standard alle Endpoints  → IP-basiert (300/min)

API-Key-Bucket: sha256(X-API-Key)[:24] → jeder Key hat eigenes Kontingent
```

## Datenfluss: Media-Upload

```
Browser → POST /aufgabe/{id}/medien (multipart)
           │
      filetype.guess() → MIME-Validierung
      Größen-Check
      Pillow / ffmpeg (Re-encode)
           │
      UUID.ext + UUID_thumb → app_storage/incident_media/
      INSERT task_media (DB)
           │
      200 _task_media.html (HTMX-Partial, DOM-Swap)
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
