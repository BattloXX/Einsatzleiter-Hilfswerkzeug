# Updates einspielen

← [Zurück zur Startseite](Home)

## Standard-Update-Prozess

```bash
cd /home/clp-einsatz/htdocs/einsatzleiter
source .venv/bin/activate

# 1. Aktuellen Stand sichern:
mysqldump -u einsatzleiter -p einsatzleiter --single-transaction > ../backup_vor_update.sql

# 2. Neuen Code holen:
git pull origin main

# 3. Abhängigkeiten aktualisieren:
pip install -e ".[dev]"

# 4. Datenbankmigrationen ausführen:
alembic upgrade head

# 5. Dienst neu starten:
sudo systemctl restart einsatzleiter

# 6. Status prüfen:
sudo systemctl status einsatzleiter
journalctl -u einsatzleiter -n 20
```

## Prüfen ob Migrationen ausstehen

```bash
alembic current   # Aktuelle Revision
alembic heads     # Neueste Revision im Code
```

Falls sie sich unterscheiden: `alembic upgrade head` ausführen.

## Rollback nach fehlgeschlagenem Update

```bash
# Zur vorherigen Alembic-Revision:
alembic downgrade -1

# Code auf vorherigen Stand zurück:
git log --oneline -5
git checkout <commit-hash>

# Dienst neu starten:
sudo systemctl restart einsatzleiter
```

## Update-Frequenz

Regelmäßige Updates werden als GitHub Releases veröffentlicht. Empfohlen:
- **Kritische Fixes:** sofort einspielen
- **Feature-Updates:** außerhalb der Einsatzsaison (z.B. Winter)
- **Sicherheits-Updates:** innerhalb 48 Stunden

## Wartungsmodus

Für größere Updates kann eine Wartungsseite geschaltet werden:

```bash
# In NGINX-Konfiguration (CloudPanel Vhost):
# Temporär auf Wartungsseite umleiten
```

---

**Nächster Schritt:** [Troubleshooting](Installation-Troubleshooting)
