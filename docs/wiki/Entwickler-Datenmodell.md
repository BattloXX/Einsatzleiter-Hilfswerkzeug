# Datenmodell

← [Zurück zur Startseite](Home)

## Überblick

Alle Tabellen haben: `id BIGINT PK AUTO_INCREMENT`, `created_at DATETIME UTC`. MariaDB 10.11, InnoDB, UTF8MB4.

`TenantScoped`-Modelle erhalten automatisch ein `org_id`-Feld und werden via SQLAlchemy `do_orm_execute`-Event auf die aktive Org gefiltert.

## Organisationen (Multi-Tenancy)

```
fire_dept
  id, slug (UNIQUE), name, color
  is_home_org, is_active
  deleted_at (NULL = aktiv, gesetzt = Soft-Delete)
  logo_path, contact_email, contact_phone, street, city
  timezone (IANA, NULL = DEFAULT_TIMEZONE)
  fallback_lat, fallback_lng
  short_code (max. 3 Zeichen, z.B. "WOL")
  storage_quota_bytes (NULL = unbegrenzt)
  withdraw_press_factor, withdraw_press_reserve

org_settings                     ← 1:1 zu fire_dept
  id, org_id FK (UNIQUE)
  primary_color, footer_text
  mi_auto_adopt
  autoclose_enabled (NULL = global), autoclose_after_hours, autoclose_grace_minutes
```

## Stammdaten (TenantScoped = automatisch nach org_id gefiltert)

```
vehicle_master
  id, dept_id FK → fire_dept, code, name, type
  is_first_train, display_order, active, deleted
  bos_override

member  [TenantScoped: org_id]
  id, org_id FK, lastname, firstname, phone, email, active

qualification
  id, code (AGT|MA|GK|ZK|EL|TF|TM|JF), label
  is_einsatzleiter, is_gruppenkommandant

member_qualification (m:n)
  member_id FK, qualification_id FK, valid_until

alarm_type  [TenantScoped: org_id]
  id PK (bigint), org_id FK
  code (T1..T9, F1..F4)
  category (Technik|Feuer)
  default_first_train_only, notify_neighbors

task_suggestion  [TenantScoped: org_id]
  id, org_id FK, alarm_type_id FK, text, display_order

message_suggestion  [TenantScoped: org_id]
  id, org_id FK, alarm_type_id FK, text

lage_hint  [TenantScoped: org_id]
  id, org_id FK, text, display_order

default_message  [TenantScoped: org_id]
  id, org_id FK, alarm_type_id FK, text, due_after_sec

seed_template
  id, profile (UNIQUE), label, bos
  (JSON-Speicher für Alarmtypen, Vorlagen, Lage-Hinweise)
```

## Authentifizierung

```
user
  id, username (UNIQUE), password_hash (bcrypt)
  display_name, email, active, last_login_at
  org_id FK → fire_dept (NULL = system_admin ohne Org)
  failed_login_count, locked_until

role
  id, code (UNIQUE: system_admin|org_admin|admin|incident_leader|...), label

user_role (m:n)
  user_id FK, role_id FK

api_key
  id, key_hash (SHA-256), label
  org_id FK → fire_dept
  created_by_user_id FK?, expires_at, revoked_at, last_used_at

device_token                     ← Tablet/Geräte-Auto-Login
  id, user_id FK, token_hash, label, revoked_at, last_used_at

audit_log
  id, user_id FK?, api_key_id FK?
  org_id FK?
  action, entity_type, entity_id, payload_json, ip

push_subscription
  id, user_id FK, endpoint, p256dh, auth
```

## Einladungen

```
org_invitation
  id, org_id FK, token_hash (UNIQUE), email, admin_name
  created_by_user_id FK, expires_at, used_at
```

## Einsätze

```
incident
  id, external_key
  UNIQUE(primary_org_id, external_key)   ← Idempotenz je Org
  primary_org_id FK → fire_dept
  nummer, alarm_type_id FK
  status (active|closed|archived)
  started_at, closed_at
  incident_leader_user_id FK?, is_exercise
  address_street, address_no, address_city, address_lat, address_lng
  report_text, reason

incident_org  (m:n: Kollaboration)
  incident_id FK, org_id FK
  added_at, added_by_user_id FK?

incident_column
  id, incident_id FK, code, title, is_fixed, display_order

incident_vehicle
  id, incident_id FK, column_id FK?
  vehicle_master_id FK, commander_member_id FK?
  display_order, removed_at, org_color_override

task
  id, incident_id FK, column_id FK?, vehicle_id FK?
  title, detail
  is_done, done_at, is_cancelled, cancelled_at, display_order
  source (manual|api|ai_suggestion|template)

task_media
  id, task_id FK, incident_id FK
  file_type (image|pdf|video), original_filename
  stored_path, thumb_path, width, height, duration_sec, file_size_bytes

message
  id, incident_id FK
  title, detail, due_after_sec, due_at
  popup_shown, is_done, is_cancelled, display_order

rescued_person
  id, incident_id FK
  gender, person_group, age_range, name, location, vehicle_id FK?

incident_log            ← sichtbares Verlaufsprotokoll
  id, incident_id FK, ts, level (info|warn|alert)
  user_id FK?, text, entity_type?, entity_id?

incident_change         ← granulares Änderungslog (Zeitreise)
  id, incident_id FK, ts, action
  entity_type, entity_id?
  before_json (LONGTEXT), after_json (LONGTEXT)
  user_id FK?, api_key_id FK?, ip

incident_token          ← QR-Login-Tokens
  id, incident_id FK, token_hash
  issued_by_user_id FK?, target_user_id FK?, revoked_at
```

## Atemschutzüberwachung

```
breathing_troop
  id, incident_id FK, vehicle_id FK?
  name, status (bereit|im_einsatz|rueckzug|zurueck|erholt)
  task_text, start_press_avg
  entry_at, withdraw_press_calc, withdraw_at, back_at, notes

troop_member
  id, troop_id FK, member_id FK?, free_text_name
  role (truppfuehrer|truppmann)
  start_press, withdraw_press, back_press

pressure_log
  id, troop_id FK, ts, member_id FK?
  pressure_bar, recorded_by_user_id FK?
```

## KI-Prompts

```
ai_prompt_version  [TenantScoped: org_id]
  id, org_id FK
  prompt_key (report|task_suggestions|lage_hints|situation|mi_prioritize)
  content (LONGTEXT), version_number
  created_by_user_id FK?, is_active
```

## System-Einstellungen

```
system_settings          ← Key-Value-Store für globale Werte
  id, key (UNIQUE), value (TEXT)
  (smtp_host, smtp_password, vapid_*, ai_enabled, incident_autoclose_*, ...)
```

## Lagekarte / Großschadenslage

```
lagekarte_token          ← Read-only GeoJSON-Feed-Tokens
  id, org_id FK, token_hash, label, revoked_at

major_incident_*         ← Großschadenslage (Phasen-Kanban, Einsatzstellen, Stab, ...)
  (siehe app/models/major_incident.py)
```

## Wichtige Indexe

```sql
-- Idempotenz-Check (je Org):
UNIQUE INDEX ON incident(primary_org_id, external_key)

-- Aktive Einsätze schnell finden:
INDEX ON incident(status, started_at)
INDEX ON incident(primary_org_id, status)

-- Änderungslog zeitlich sortiert:
INDEX ON incident_change(incident_id, ts)

-- Pressure-Log je Trupp:
INDEX ON pressure_log(troop_id, ts)

-- Tenant-Filter:
INDEX ON member(org_id)
INDEX ON alarm_type(org_id)
INDEX ON task_suggestion(org_id)
```
