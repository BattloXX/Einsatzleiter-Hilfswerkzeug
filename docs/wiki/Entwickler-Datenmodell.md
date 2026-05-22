# Datenmodell

← [Zurück zur Startseite](Home)

## Überblick

Alle Tabellen haben: `id BIGINT PK AUTO_INCREMENT`, `created_at DATETIME`, außer wo anders angegeben. MariaDB 10.11, InnoDB, UTF8MB4.

## Stammdaten

```
fire_dept ──────────────────────────────────┐
  id, slug, name, color                     │
  withdraw_press_factor, withdraw_press_reserve │
       │                                    │
vehicle_master ─────────────────────────────┘
  id, dept_id FK, code, name, type
  is_first_train, display_order, active

member
  id, lastname, firstname, phone, email, active

qualification
  id, code (AGT|MA|GK|ZK|EL|TF|TM|JF), label

member_qualification (m:n)
  member_id FK, qualification_id FK, valid_until

alarm_type
  code PK (T1..T7, F1..F4)
  category (Technik|Feuer)
  default_first_train_only, notify_neighbors

task_suggestion
  id, alarm_type_code FK, text, display_order

lage_hint
  id, text, display_order

default_message
  id, alarm_type_code FK, text, due_after_sec
```

## Authentifizierung

```
user
  id, username (UNIQUE), password_hash
  display_name, active, last_login_at

role
  id, code (UNIQUE: admin|incident_leader|...), label

user_role (m:n)
  user_id FK, role_id FK

api_key
  id, key_hash, label
  created_by_user_id FK, expires_at, revoked_at, last_used_at

audit_log
  id, user_id FK?, api_key_id FK?
  action, entity_type, entity_id, payload_json, ip

push_subscription
  id, user_id FK, endpoint, p256dh, auth
```

## Einsätze

```
incident
  id, external_key (UNIQUE), nummer
  alarm_type_code FK, status (active|closed|archived)
  started_at, closed_at
  incident_leader_user_id FK?, is_exercise
  address_street, address_no, address_city
  report_text, reason

incident_column
  id, incident_id FK, code, title
  is_fixed, display_order

incident_vehicle
  id, incident_id FK, column_id FK?
  vehicle_master_id FK, commander_member_id FK?
  display_order, removed_at, org_color_override

task
  id, incident_id FK, column_id FK?, vehicle_id FK?
  title, detail
  is_done, done_at, is_cancelled, cancelled_at, display_order

message
  id, incident_id FK
  title, detail, due_after_sec, due_at
  popup_shown, is_done, is_cancelled, display_order

rescued_person
  id, incident_id FK
  gender, person_group, age_range, name, location
  vehicle_id FK?

incident_log          ← sichtbares Verlaufsprotokoll
  id, incident_id FK, ts, level (info|warn|alert)
  user_id FK?, text, entity_type?, entity_id?

incident_change       ← granulares Änderungslog (ersetzt Snapshots)
  id, incident_id FK, ts, action
  entity_type, entity_id?
  before_json (LONGTEXT), after_json (LONGTEXT)
  user_id FK?, api_key_id FK?, ip

incident_token        ← QR-Tokens
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

## Wichtige Indexe

```sql
-- Idempotenz-Check:
UNIQUE INDEX ON incident(external_key)

-- Aktive Einsätze schnell finden:
INDEX ON incident(status, started_at)

-- Änderungslog zeitlich sortiert:
INDEX ON incident_change(incident_id, ts)

-- Pressure-Log je Trupp:
INDEX ON pressure_log(troop_id, ts)
```
