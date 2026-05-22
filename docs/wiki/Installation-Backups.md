# Backups

← [Zurück zur Startseite](Home)

## Automatische Datenbank-Dumps (CloudPanel)

CloudPanel bietet integrierte Backups. Einrichten unter:  
**Settings** → **Backup** → tägliche Sicherung aktivieren.

Manueller Dump:
```bash
mysqldump -u einsatzleiter -p einsatzleiter \
    --single-transaction \
    --routines \
    --triggers \
    > /home/clp-einsatz/backups/einsatzleiter_$(date +%Y%m%d_%H%M%S).sql
```

## Backup-Verzeichnis anlegen

```bash
mkdir -p /home/clp-einsatz/backups
chmod 700 /home/clp-einsatz/backups
```

## Cron-Job für stündliche Sicherung

```bash
crontab -e
```

```cron
# Stündlicher DB-Dump (behalte die letzten 72 Stunden):
0 * * * * mysqldump -u einsatzleiter -pPASSWORT einsatzleiter \
    --single-transaction > /home/clp-einsatz/backups/hourly_$(date +\%Y\%m\%d_\%H).sql
# Alte Dumps löschen (älter als 3 Tage):
30 * * * * find /home/clp-einsatz/backups -name "hourly_*.sql" -mtime +3 -delete
```

## Backup wiederherstellen

```bash
# Alle Tabellen sichern (falls was schiefgeht):
mysqldump -u einsatzleiter -p einsatzleiter > vor_restore.sql

# Wiederherstellen:
mysql -u einsatzleiter -p einsatzleiter < /home/clp-einsatz/backups/einsatzleiter_20260522_030000.sql
```

## Was wird gesichert?

| Was | Warum |
|-----|-------|
| MariaDB-Datenbank | Alle Einsätze, Mitglieder, Konfiguration |
| `.env`-Datei | Secrets, VAPID-Keys (extra sichern!) |
| `app/static/img/` | Falls eigene Logos hochgeladen |

Die Codebasis ist via Git versioniert und muss nicht gesondert gesichert werden.

## Offsite-Backup

Für eine zweite Sicherung außerhalb des Servers:

```bash
# Beispiel: rsync auf NAS im Feuerwehrgebäude:
rsync -av /home/clp-einsatz/backups/ \
    user@nas.feuerwehr-wolfurt.local:/backups/einsatzleiter/
```

---

**Nächster Schritt:** [Updates einspielen](Installation-Updates)
