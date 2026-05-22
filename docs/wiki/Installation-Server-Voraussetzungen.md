# Server-Voraussetzungen

← [Zurück zur Startseite](Home)

## Betriebssystem

**Debian 12 Bookworm** (empfohlen) oder Ubuntu 22.04 LTS.

## CloudPanel

[CloudPanel](https://www.cloudpanel.io) übernimmt das Hosting-Management (NGINX, SSL, Datenbanken, Cron-Jobs). Installation nach der offiziellen Anleitung:

```bash
curl -sS https://installer.cloudpanel.io/ce/v2/install.sh -o install.sh
sudo bash install.sh
```

## Python 3.12

```bash
# Prüfen ob Python 3.12 vorhanden:
python3.12 --version

# Falls nicht:
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv python3.12-dev
```

## Systempakete für WeasyPrint und MariaDB

WeasyPrint (PDF-Generierung) benötigt Pango/Cairo. Der MariaDB-Connector braucht die Dev-Header.

```bash
sudo apt-get install -y \
    libmariadb-dev \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    build-essential \
    git
```

## Ports und Firewall

Der App-Prozess lauscht intern auf `127.0.0.1:8000`. Nach außen ist **nur NGINX** (Port 80/443) erreichbar. Kein direkter Zugriff auf Port 8000 erforderlich.

```bash
# Beispiel mit ufw:
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp   # SSH
sudo ufw enable
```

## Mindest-Hardware

| Komponente | Minimum | Empfohlen |
|------------|---------|-----------|
| CPU | 1 vCore | 2 vCores |
| RAM | 1 GB | 2 GB |
| Disk | 10 GB | 20 GB SSD |
| Netz | 10 Mbit/s | 100 Mbit/s |

Für 10 gleichzeitige Browser-Sessions reicht 1 GB RAM. WeasyPrint für große PDFs kann kurz ~300 MB extra benötigen.

---

**Nächster Schritt:** [Datenbank einrichten](Installation-Datenbank-Einrichtung)
