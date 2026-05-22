# Atemschutzüberwachung

← [Zurück zur Startseite](Home)

## Ansicht öffnen

Im Einsatz-Board: Tab **Atemschutz** (oder direkt `/einsatz/{id}/atemschutz`)

Die Atemschutz-Ansicht ist für alle Rollen lesbar. Änderungen dürfen:
- Admin
- Einsatzleiter
- AS-Überwacher

## Trupp anlegen

1. **+ Neuer Trupp** klicken
2. Name: z.B. „Trupp 1 – RLF" (Vorschlag kann angepasst werden)
3. **Truppführer** auswählen (aus Mannschaftsregister oder Freitext)
4. **Truppmann** auswählen
5. Wenn ein Mitglied **keine AGT-Qualifikation** hat, erscheint eine orange Warnung
6. Optional: **Fahrzeug** zuweisen und **Aufgabe** beschreiben
7. **Speichern**

## Anfangsdrücke eintragen

Nach Trupp-Anlage: Für jedes Mitglied den Flascheninnendruck in bar eintragen:

| Mitglied | Anfangsdruck |
|----------|-------------|
| Truppführer | z.B. 300 bar |
| Truppmann | z.B. 295 bar |

**Rückzugsdruck wird automatisch berechnet:**

```
Rückzugsdruck = Anfangsdruck × 0,5 + 10 bar (Sicherheitsreserve)
Beispiel: 300 bar × 0,5 + 10 = 160 bar
```

Der ungünstigste (niedrigste) Rückzugsdruck aller Mitglieder gilt für den gesamten Trupp.

## Einsatz starten

**▶ Einsatz starten** klicken → `entry_at` wird gesetzt → Stoppuhr läuft.

Jetzt ist der Trupp im Status **Im Einsatz**.

## Druckupdates eintragen

Während des Einsatzes: Neue Druckwerte in die Felder eintragen → **Druck protokollieren**.

Druckwerte werden in der `pressure_log`-Tabelle aufgezeichnet.

## Warnungen

| Warnlevel | Bedingung | Anzeige |
|-----------|-----------|---------|
| **Normal** | Über 75% des Anfangsdrucks | Grüner Balken |
| **Gelb** | Unter 75% des Anfangsdrucks | Gelber Balken + Warnung |
| **Rot / Rückzug!** | Am oder unter Rückzugsdruck | Roter pulsierender Balken + akustischer Alarm |

Bei **Rot** erscheint eine große Warnung und ein Ton wird abgespielt (falls Ton vom Browser erlaubt).

## Status-Wechsel

| Von | Nach | Bedeutung |
|-----|------|-----------|
| Bereit | Im Einsatz | Trupp betritt den Gefahrenbereich |
| Im Einsatz | Rückzug | Trupp hat Rückzugsdruck erreicht oder wird zurückgerufen |
| Rückzug | Zurück | Trupp hat den Gefahrenbereich verlassen |
| Zurück | Erholt | Trupp ist wieder einsatzbereit |

## Trupp zurückrufen

**Rückzug** klicken → `withdraw_at` wird gesetzt. Alle Karten zeigen „RÜCKZUG!!" in rot.

## Abschlussdruck eintragen

Nach dem Einsatz: Restdrücke der Flaschen eintragen → Verbrauch wird berechnet und im PDF-Bericht ausgegeben.

## PDF-Protokoll

Im Einsatz-Abschlussbericht gibt es eine eigene Seite „Atemschutz-Protokoll" mit allen Trupps, Druckwerten, Zeiten und berechneten Atemluftmengen.
