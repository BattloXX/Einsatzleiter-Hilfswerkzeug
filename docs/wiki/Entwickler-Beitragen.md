# Beitragen

← [Zurück zur Startseite](Home)

## Branch-Strategie

```
main           – Stabile, produktionsreife Version
develop        – Integrations-Branch für Features
feature/xyz    – Feature-Branches (von develop abzweigen)
fix/xyz        – Bugfix-Branches (von main oder develop)
```

## Arbeitsablauf

```bash
# Feature:
git checkout develop
git pull origin develop
git checkout -b feature/atemschutz-verbesserung

# ... Entwicklung ...

git add -p    # Interaktiv, nur relevante Änderungen
git commit -m "feat: Rückzugsdruck-Warnung akustisch verbessern"
git push origin feature/atemschutz-verbesserung

# Pull Request: feature/* → develop
# Nach Review und CI: merge
# Für Releases: develop → main
```

## Commit-Format (Conventional Commits)

```
<typ>: <beschreibung>

[optionaler body]
```

| Typ | Bedeutung |
|-----|-----------|
| `feat` | Neues Feature |
| `fix` | Bugfix |
| `docs` | Nur Dokumentation |
| `refactor` | Code-Umstrukturierung ohne Feature/Fix |
| `test` | Tests hinzugefügt oder verbessert |
| `chore` | Build-System, Dependencies |
| `style` | Formatierung, kein funktionaler Einfluss |

**Beispiele:**
```
feat: QR-Code-Gültigkeit an Einsatzdauer binden
fix: Rückzugsdruck bei 0-bar-Anfangsdruck korrekt berechnen
docs: Atemschutz-Wiki-Seite ergänzen
test: Integrations-Tests für API-Idempotenz
```

## Code-Qualität

Vor dem Commit:

```bash
ruff check app/ --fix     # Lint + Auto-Fix
mypy app/ --ignore-missing-imports   # Type-Check
pytest tests/ -v          # Tests
```

CI schlägt fehl bei Lint-Fehlern oder fehlgeschlagenen Tests.

## Pull Request Checkliste

- [ ] Branch von `develop` abgezweigt
- [ ] Commits im Conventional-Commit-Format
- [ ] `ruff check` ohne Fehler
- [ ] `mypy` ohne neue Fehler
- [ ] Tests hinzugefügt/aktualisiert
- [ ] `pytest tests/` läuft durch
- [ ] Bei Datenbankänderungen: Alembic-Migration vorhanden

## Datenbankmigrationen

Bei neuen/geänderten Models immer eine Migration erstellen:

```bash
alembic revision --autogenerate -m "beschreibung"
```

Die generierte Datei in `alembic/versions/` überprüfen (autogenerate erkennt nicht alles korrekt) und committen.

## Design-Prinzipien

- **Einfachheit vor Cleverness**: Das Tool wird im Stress-Szenario bedient. Lieber eine Funktion weniger als eine unverständliche.
- **Keine Dependencies ohne klaren Nutzen**: Jede neue Dependency erhöht die Komplexität.
- **Keine Mocks in Tests**: Echte Datenbank-Tests verhindern Divergenz.
- **Server is Source of Truth**: Client-State ist nur für UI-Komfort, nie für Entscheidungen.

## Issues und Bugs

Issues auf GitHub: https://github.com/BattloXX/FWWO-Einsatzleiter-Hilfswerkzeug/issues

Bug-Report enthält:
1. Beschreibung was erwartet wird
2. Beschreibung was tatsächlich passiert
3. Schritte zum Reproduzieren
4. Browser, OS, Einsatz-ID (falls relevant)
