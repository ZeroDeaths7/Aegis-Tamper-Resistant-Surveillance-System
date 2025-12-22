# AegisAI – Tamper‑Resistant Surveillance System

AegisAI is a tamper‑aware surveillance system that **detects and logs physical attacks, environmental interference, and replay attacks in real time** using computer vision, cryptography, and structured incident logging.

The system is built as a **single‑camera demo stack** with:

- OpenCV‑based video processing
- Multiple tamper‑detection modules (blur, shake, glare, liveness, reposition, blackout)
- A **cryptographic watermark pipeline** to prove that video was captured live
- A **SQLite database** for incident logging and analytics
- A **web UI (frontend)** connected via Socket.IO for real‑time monitoring

This repository is optimized for **explainability and mentorship**: every major module is documented in [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md).

---

## Table of Contents

- [Concept & Threat Model](#concept--threat-model)
- [Core Features](#core-features)
- [Repository Structure](#repository-structure)
- [Key Detection Modules](#key-detection-modules)
  - [Blur Detection](#blur-detection)
  - [Shake & Reposition](#shake--reposition)
  - [Glare Detection & Rescue](#glare-detection--rescue)
  - [Liveness & Blackout](#liveness--blackout)
  - [HMAC Watermark Validation](#hmac-watermark-validation)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the App](#running-the-app)
- [Configuration](#configuration)
- [Incidents, Storage & Logs](#incidents-storage--logs)
- [Testing](#testing)
- [Limitations & Future Work](#limitations--future-work)
- [License](#license)
- [Contact](#contact)

---

## Concept & Threat Model

Traditional CCTV systems can be silently defeated by:

- Covering or defocusing the lens
- Shaking or repositioning the camera
- Shining strong light (flashlight, car headlights, sunlight) into the lens
- Freezing or looping the video feed
- Playing back **old video** to spoof “live” footage

**AegisAI** treats the camera as an actively defended sensor:

- It continuously monitors the **video statistics and motion patterns** to detect:
  - Blur / obstruction
  - Vibration vs actual camera re‑aiming
  - Glare and over/under‑exposure
  - Frozen or replayed feeds
  - Full blackout
- It embeds and validates a **time‑based HMAC watermark** inside the video so that uploaded clips can be verified as **live and recent**, not replays.

The goal is not just detection, but **forensic traceability**: every incident is logged with type, timing and auxiliary data in a local database.

---

## Core Features

- **Blur / Obstruction Detection**  
  Uses Laplacian variance to detect when the lens is intentionally or accidentally obscured.

- **Shake & Camera Reposition Detection**  
  Uses dense optical flow (Farneback) + motion history to distinguish:
  - Brief vibration (shake) vs
  - Sustained directional camera rotation (reposition).

- **Glare Detection & Rescue**  
  Detects histogram signatures of glare; optionally applies CLAHE + sharpening to rescue detail from overexposed frames. Example glare frames live in `Glare_Rescue_Pics/`.

- **Liveness / Frozen‑Feed & Blackout Detection**  
  Uses frame‑difference statistics and brightness thresholds to:
  - Detect frozen or looped feeds
  - Detect lens cap / total blackout conditions.

- **HMAC Watermark for Replay‑Attack Defense**  
  - On live streams, the backend embeds a **colored square watermark** derived from an HMAC‑SHA256 of the current timestamp.  
  - On upload, the system extracts colors from the ROI and validates them against the expected HMAC sequence, with a threshold for “LIVE vs NOT_LIVE”.

- **Incident Database & Analytics**  
  - SQLite DB (`aegis.db`) storing:
    - incidents (blur, shake, glare, reposition, freeze, blackout, major_tamper)
    - audio logs
    - glare images metadata
    - liveness validation results  
  - Incident grouping logic to avoid flooding during sustained attacks.

- **Real‑Time Web UI**  
  - Backend emits frames, metrics and alert events over Socket.IO.
  - Frontend (in `Frontend/`) shows live feed, processed frames, and incident status.

For deep algorithmic details and worked examples, see:  
👉 [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)

---

## Repository Structure

High‑level layout (non‑exhaustive):

```text
.
├── app.py                     # Main backend / app entry point (Flask / Socket.IO style)
├── tamper_detector.py         # Core blur / shake / reposition / liveness logic
├── liveness.py                # Helper functions for frozen-feed / liveness checks
├── low_light.py               # Low-light handling utilities
├── dynamic_watermarker.py     # (If used) dynamic overlay / watermark helpers
├── Sensor/
│   └── glare_rescue.py        # Glare detection + CLAHE-based rescue
├── backend/
│   ├── database.py            # SQLite models and incident/audio/glare/liveness tables
│   ├── watermark_embedder.py  # HMAC timestamp → color watermark embedding
│   ├── watermark_extractor.py # ROI extraction + mean color computation
│   ├── watermark_validator.py # Frame-by-frame HMAC color validation
│   └── pocketsphinx_*.py      # Audio recognition integration (if available)
├── Frontend/                  # Web UI (JS/HTML/CSS)
├── storage/                   # Output, uploads, generated evidence, etc.
├── Glare_Rescue_Pics/         # Example images for glare experiments
├── requirements.txt           # Python dependencies
├── aegis.db                   # SQLite database (created at runtime)
├── TECHNICAL_DOCUMENTATION.md # Detailed mentor-level docs
└── tests (separate files)
    ├── test_api_response_format.py
    ├── test_camera.py
    ├── test_e2e_validation.py
    ├── test_hmac_token_format.py
    ├── test_integration.py
    ├── test_json_serialization.py
    ├── test_optical_flow.py
    ├── test_tamper_detector.py
    ├── test_video_validation_json.py
    └── test_watermarker.py
```

---

## Key Detection Modules

This section summarizes what’s implemented; the exact math / thresholds are explained in  
[TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md).

### Blur Detection

- **File:** `tamper_detector.py` → `check_blur()`
- **Method:** Laplacian variance on grayscale frames.
- **Intuition:** Sharp images have high Laplacian variance; blurred / covered images have low variance.
- **Core idea:** If Laplacian variance < `BLUR_THRESHOLD` (≈ 70.0 by default) for long enough, raise a **BLUR ALERT**.

### Shake & Reposition

- **File:** `tamper_detector.py` → `check_shake()` and `detect_camera_reposition()`
- **Method:** Dense optical flow (Farneback) across consecutive frames.
- **Shake:** 
  - Looks for high average motion magnitude but **oscillatory** (back‑and‑forth) direction.
- **Reposition:** 
  - Tracks motion history (up to 10 frames) and checks for:
    - Sustained high shift magnitude
    - **Consistent direction** over time
  - Also fires an **immediate alert** on very large single‑frame shifts (fast jerk).

### Glare Detection & Rescue

- **File:** `Sensor/glare_rescue.py`
- **Detection:** Histogram‑based “loss of detail” in grayscale:
  - Too many dark pixels, too many bright pixels, not enough mid‑tones.
- **Rescue:** CLAHE + sharpening to recover detail; extreme highlights are tamed.
- **Integration:** Controlled via flags in `app.py` (e.g. `GLARE_RESCUE_ENABLED`).

### Liveness & Blackout

- **File:** `tamper_detector.py` / `liveness.py` (as helper)
- **Frozen feed:**  
  - Uses frame‑difference sums between current and reference frame.
  - Below `LIVENESS_THRESHOLD` over a window → feed appears frozen.
- **Dynamic reference:**  
  - Reference frames are periodically updated to avoid false positives in static scenes.
- **Blackout:**  
  - Uses mean brightness < `BLACKOUT_BRIGHTNESS_THRESHOLD` as a signal for full blackout (lens cap / darkness).

### HMAC Watermark Validation

- **Files:**
  - Embedding: `backend/watermark_embedder.py`
  - Extraction: `backend/watermark_extractor.py`
  - Validation: `backend/watermark_validator.py`
- **Idea:**
  - During capture, each frame encodes a **timestamp‑based HMAC** as a small RGB square in the bottom‑right corner.
  - On uploaded videos, AegisAI:
    1. Extracts average RGB from the watermark ROI per frame.
    2. Recomputes expected HMAC colors for the corresponding timestamps.
    3. Compares via Euclidean distance in RGB space.
    4. Computes what percentage of frames match; if ≥ `LIVE_THRESHOLD` (≈ 70%), video is treated as **LIVE**.
- **Security:**  
  Without the secret key, attackers cannot forge correct colors for arbitrary timestamps, so replay attacks are detected.

All of this is described in depth with step‑by‑step examples in  
[TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md).

---

## Getting Started

### Prerequisites

- Python **3.9+**
- A working C toolchain for OpenCV / scientific libs (on Linux: `build-essential`, `cmake`; on Windows: Visual Studio Build Tools)
- FFmpeg (for full video encode/decode workflows)
- (Optional) PocketSphinx if you want audio recognition enabled
- A modern browser for the web UI

On Ubuntu/Debian‑like systems:

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-dev ffmpeg \
    build-essential libopencv-dev
```

### Installation

Clone the repository and install Python dependencies:

```bash
git clone https://github.com/ZeroDeaths7/AegisAI-tamper-resistent-surveillance-system.git
cd AegisAI-tamper-resistent-surveillance-system

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt
```

> Note: The exact dependency list lives in `requirements.txt`. If you change modules, keep that file in sync.

### Running the App

1. **Initialize the database (optional first run)**  
   On first run, `backend/database.py` is responsible for creating the `aegis.db` schema.  
   If a helper script exists (e.g. `python backend/database.py --init`), run it; otherwise just start `app.py` and it will auto‑create tables.

2. **Start the backend server**

   ```bash
   python app.py
   ```

   This will:
   - Open the camera (or video source) handled by `app.py`
   - Run tamper detection modules in real time
   - Start a web server and Socket.IO endpoint for the frontend

3. **Open the frontend**

   - If `Frontend` is a static folder served by `app.py`, browse to the URL printed in the terminal (commonly `http://localhost:5000` or `http://localhost:8000`).
   - If there is a separate frontend dev server (e.g. React/Vite), follow the instructions in `Frontend/README` (if present) and point it at the backend Socket.IO URL.

4. **Trigger some events**

   - **Blur/obstruction:** briefly cover the camera with your hand.
   - **Shake:** gently tap the camera mount.
   - **Reposition:** slowly rotate or quickly jerk the camera.
   - **Glare:** shine a flashlight into the lens or display high‑contrast images.
   - **Frozen feed simulation:** feed a pre‑encoded video or pause updates in a test harness.

   Observed behavior:
   - Real‑time metrics and alert banners in the UI.
   - New incident rows created in `aegis.db`.

---

## Configuration

Most runtime behavior is controlled via:

- **Environment variables**, **config flags**, or small constants in:
  - `tamper_detector.py`
  - `Sensor/glare_rescue.py`
  - `liveness.py`
  - `backend/watermark_*.py`
  - `backend/database.py`

Typical configuration knobs:

- **Blur module**
  - `BLUR_THRESHOLD` – Laplacian variance threshold

- **Shake & reposition**
  - `SHAKE_THRESHOLD`
  - `REPOSITION_THRESHOLD`
  - `FAST_REPOSITION_THRESHOLD`
  - `_MAX_HISTORY`
  - `DIRECTION_CONSISTENCY`

- **Glare**
  - Histogram percentage thresholds: `threshold_dark_pct`, `threshold_bright_pct`, `threshold_mid_pct`
  - CLAHE parameters: `clipLimit`, `tileGridSize`

- **Liveness**
  - `LIVENESS_THRESHOLD`
  - `LIVENESS_CHECK_INTERVAL`
  - `LIVENESS_ACTIVATION_TIME`
  - `BLACKOUT_BRIGHTNESS_THRESHOLD`

- **Watermark validation**
  - `LIVE_THRESHOLD` (percentage of frames that must match)
  - Secret key for HMAC (in `watermark_embedder.py` / `watermark_validator.py`)

If you deploy this anywhere non‑demo‑like, **move secrets to environment variables or a secure config**, and rotate keys.

---

## Incidents, Storage & Logs

- **Database:** `aegis.db` (SQLite)
- **Main tables** (see [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) for schema):

  - `incidents` – blur, shake, glare, reposition, freeze, blackout, major_tamper
  - `audio_logs` – recognized text tied to incidents
  - `glare_images` – file paths and stats for stored glare frames
  - `liveness_validations` – per‑upload validation results (live/not_live, JSON frame stats)

- **Retention behavior:**
  - In‑memory tracking only keeps a small rolling window (e.g. last 5 incidents) to avoid overload.
  - Full history is persisted in the DB for offline analysis.

> If you want to inspect the DB directly, open `aegis.db` with any SQLite browser (e.g. `sqlite3` CLI, DB Browser for SQLite).

---

## Testing

This repo includes multiple focused tests to validate:

- API responses / JSON format – `test_api_response_format.py`
- Camera and capture behavior – `test_camera.py`
- End‑to‑end validation – `test_e2e_validation.py`
- HMAC token / watermark format – `test_hmac_token_format.py`, `test_watermarker.py`
- Optical flow & reposition detection – `test_optical_flow.py`, `test_tamper_detector.py`
- Video validation JSON structure – `test_video_validation_json.py`
- Serialization helpers – `test_json_serialization.py`
- Integration glue – `test_integration.py`

To run the full test suite:

```bash
pytest
```

(Ensure your virtualenv is activated and `pytest` is installed via `requirements.txt`.)

Some tests may require sample videos / images and can be sensitive to environment differences (e.g. OpenCV version).

---

## Limitations & Future Work

This is a **prototype / research‑grade** system, not a product:

- Single‑camera focus; multi‑camera orchestration is not implemented.
- No production‑grade auth/RBAC for the web UI.
- Watermark key management is simplified for demonstration.
- No distributed ledger or external timestamp anchoring (though the design is compatible).

Potential next steps:

- Multi‑camera support and centralized controller
- Hardened key management plus HSM / TPM integration
- Exportable “evidence packages” with verification CLI
- CI pipeline for automatic tests on every commit
- More advanced AI models for semantic event detection

---

## License

This project is released under the **MIT License**.  
See [LICENSE](LICENSE) for full terms.

---

## Contact

- Authors: **Prateek,Mevin,Rajeev,Abhiram**  
- Repository: [AegisAI‑tamper‑resistent‑surveillance‑system](https://github.com/ZeroDeaths7/AegisAI-tamper-resistent-surveillance-system)

For questions, issues, or contributions:

- Open a GitHub issue on this repository, or
- Fork and submit a pull request with a clear description and tests where appropriate.

For a deep dive into the math and design decisions, start with:  
👉 [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)
