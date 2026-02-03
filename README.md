# AegisAI – Tamper-Resistant Surveillance System

AegisAI is a professional-grade surveillance platform combining real-time AI tamper detection with cryptographic evidence preservation. It identifies physical attacks (blurring, shaking, repositioning) and digital replay attacks using computer vision and robust watermarking.

---

## Dashboard Overview

The real-time dashboard provides visualization of camera feeds, tamper metrics, and incident logs with toggleable defense modules.

| Primary Dashboard View | Video Integrity & Analytics |
|:---:|:---:|
| ![Main Dashboard](assets/frontend/dashboard_main.png) | ![Video Analysis](assets/frontend/dashboard_video.png) |

---

## Key Capabilities

- **Tamper Detection**: Real-time identification of blur, shake, and repositioning.
- **Glare Rescue**: Detail recovery from overexposed frames using CLAHE.
- **Cryptographic Security**: HMAC-SHA256 frame watermarking to prevent replay attacks.
- **Forensic Logging**: SQL-backed incident tracking and liveness verification.

### Glare Rescue Performance
| Glare Detection | Recovery Process | Restored Output |
|:---:|:---:|:---:|
| ![Glare 1](assets/debug/glare_rescue/glare_detection.png) | ![Glare 2](assets/debug/glare_rescue/glare_recovery.png) | ![Glare 3](assets/debug/glare_rescue/glare_output.png) |

---

## Technical Architecture

- **Backend**: Python/Flask-SocketIO handling computer vision (OpenCV) and cryptography.
- **Frontend**: HTML5/JS/CSS real-time monitoring dashboard.
- **Security**: HMAC-SHA256 token embedding for frame-level integrity.
- **Database**: SQLite for auditable incident logs and metadata.

---

## Quick Start

### Installation
```powershell
# Clone and setup
git clone https://github.com/ZeroDeaths7/AegisAI-tamper-resistent-surveillance-system.git
cd AegisAI-tamper-resistent-surveillance-system
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Execution
```powershell
python app.py
```
Access the dashboard at `http://localhost:5000`.

---

## Testing
Run the automated test suite to verify detection and integrity modules:
```bash
pytest
```

---

## Authors & License
- **Authors**: Prateek, Mevin, Rajeev, Abhiram
- **License**: MIT License
