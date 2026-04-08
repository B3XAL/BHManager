<p align="center">
  <img src="https://raw.githubusercontent.com/B3XAL/BHManager/main/docs/banner.png" alt="BHManager banner" width="680"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Streamlit-1.35-FF4B4B?style=flat-square&logo=streamlit&logoColor=white" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/Docker-required-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/badge/BloodHound-CE-red?style=flat-square" alt="BloodHound CE"/>
  <img src="https://img.shields.io/badge/version-v1.2-brightgreen?style=flat-square" alt="Version"/>
</p>

<p align="center">
  A web dashboard to manage multiple BloodHound Community Edition instances from a single interface.<br>
  Built for pentesters and red teamers handling several clients at the same time.
</p>

---

## Preview

<p align="center">
  <img src="https://raw.githubusercontent.com/B3XAL/BHManager/main/docs/dashboard.png" width="700"/>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/B3XAL/BHManager/main/docs/deploy.png" width="700"/>
</p>

---

## What is this?

When running multiple red team or pentesting engagements in parallel, you need **separate BloodHound instances per client** — different data, different ports, no cross-contamination. Managing that manually with Docker is tedious. BHManager gives you a fast, dark web UI to:

- 🚀 Spin up a new BloodHound CE instance in seconds
- 📊 See all instances at a glance with live status
- ⚙️ Start / Stop / Restart / Reset password with one click
- 📋 View real-time container logs with color highlighting
- 📦 Export any instance to a `.tar` and import it on another machine — data, credentials and all
- 🗑  Delete instances and all their data (with double confirmation)

---

## Requirements

| Tool | Min version |
|------|------------|
| Docker | 24+ (with Compose v2 plugin) |
| Linux / macOS | — |
| Windows | — |

---

## Quick start

```bash
git clone https://github.com/B3XAL/BHManager.git
cd BHManager
docker compose up -d --build
# open http://localhost:8501
```

First build takes ~1 minute (downloads Docker CLI + Python deps). Subsequent starts are instant.

---

## How it works

```
  Browser → localhost:8501
       │
       ▼
  Container: bhce-manager  (Streamlit)
       │
       │  /var/run/docker.sock
       ▼
  Host Docker daemon
       ├── bhce_client1:  bloodhound + neo4j + postgres
       ├── bhce_client2:  bloodhound + neo4j + postgres
       └── bhce_client3:  bloodhound + neo4j + postgres
```

Each BloodHound instance is an independent Docker Compose project (`bhce_<n>`).
Instances live in `./instances/` and **survive manager restarts**.

---

## Features

| Page | Description |
|------|-------------|
| **Dashboard** | Live overview — status, ports, URL and password per instance |
| **New Instance** | Automated deploy with free-port verification, live log output |
| **Manage** | Start / Stop / Restart / Reset password / Delete |
| **Logs** | Color-coded log viewer (ERROR / WARN / INFO), auto-refresh |
| **Import / Export** | Backup and restore full instances across machines (see below) |
| **Settings** | System diagnostics, tool versions, Docker info |

### Import / Export

Move a complete BloodHound instance (data + credentials + config) between machines with a single `.tar` file.

**Export**
1. Select the client instance
2. Choose export mode:
   - **Without images** *(recommended)* — volumes + config only. Images are pulled from Docker Hub automatically on import. Typical size: 50 MB – 2 GB depending on the AD dataset.
   - **With images** — fully self-contained, no internet needed on the target machine. Typical size: 3–8 GB.
3. The instance is briefly stopped for data consistency, then automatically restarted.
4. Download the resulting `<client>_bhce_export.tar`.

**Import**
1. Upload the `.tar` — the UI shows a preview with instance name, export date and original ports.
2. Ports are reused if free on the new machine, otherwise new ones are auto-assigned.
3. Docker images are loaded (if included) or pulled, volumes are restored, and the instance starts automatically.

> The upload limit is set to **2 GB** by default. To raise it, change `STREAMLIT_SERVER_MAX_UPLOAD_SIZE` in `docker-compose.yml`.

---

### Instance creation flow

1. Sanitize name (`a-z`, `0-9`, `_`, `-` only)
2. Download `docker-compose.yml` + `bloodhound.config.json` from SpecterOps
3. Assign ports — random in range 10000–60000, verified free on host before use
4. Patch compose + config with assigned ports
5. `docker compose up -d`
6. Poll logs until initial password appears
7. Save metadata to `.bhce_meta`

---

## Project structure

```
BHManager/
├── app.py                  ← Streamlit app (UI + logic)
├── Dockerfile              ← Manager image (Python + Docker CLI + yq)
├── docker-compose.yml      ← Manager compose
├── requirements.txt
├── docs/
│   ├── banner.png
│   ├── dashboard.png
│   └── deploy.png
└── instances/              ← Auto-created, persistent
    └── <client>/
        ├── docker-compose.yml
        ├── bloodhound.config.json
        └── .bhce_meta      ← ports + password + email
```

---

## Security

> ⚠️ The manager has full access to the host Docker daemon. Use only in controlled environments.

- Listens **only on `127.0.0.1:8501`** — not exposed to the network
- No authentication — designed for local use or behind a VPN
- For remote access: `ssh -L 8501:localhost:8501 user@your-server`

---

## Troubleshooting

**Socket error on startup**
```bash
sudo usermod -aG docker $USER && newgrp docker
```

**Password not captured after deploy**
Go to **Logs → bloodhound** and look for `Initial Password Set To:`.
On slow hardware the 60-attempt timeout (×3s) may not be enough — check logs manually.

**Port conflict when entering ports manually**
Auto mode verifies ports before assigning. If you enter them manually, make sure they're free.

---

## Links

- [BloodHound CE](https://github.com/SpecterOps/BloodHound)
- [SharpHound](https://github.com/SpecterOps/SharpHound/releases)
- [AzureHound](https://github.com/SpecterOps/AzureHound)
- [BloodHound Docs](https://support.bloodhoundenterprise.io)

---

<p align="center"><sub>Built for the controlled chaos of red teaming. Use responsibly.</sub></p>
