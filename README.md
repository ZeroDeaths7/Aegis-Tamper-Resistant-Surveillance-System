# AegisAI — Tamper-Resistant Surveillance System

AegisAI is a professional-grade, end-to-end surveillance platform that combines real-time **AI-driven tamper detection** with **cryptographic evidence preservation**. It is designed to identify physical attacks (blurring, shaking, repositioning), environmental interference, and digital replay attacks using a hybrid approach of computer vision and robust watermarking.

---

## 🛠️ Key Features

### 🛡️ Active Tamper Detection
- **Blur Detection**: Detects lens obstruction or intentional refocusing.
- **Shake Detection**: Identifies physical force, vibrations, or mount tampering.
- **Glare Rescue**: Intelligently recovers detail from frames washed out by high-intensity light (e.g., flashlights).
- **Reposition Detection**: Uses directional flow consistency to detect if a camera has been slowly pointed away.

### 🔐 Cryptographic Integrity
- **Live Proof via Watermarking**: Every frame is embedded with a time-synced HMAC-SHA256 color token.
- **Replay Protection**: Prevents attackers from using pre-recorded footage by validating tokens against current server state.
- **Auditable Evidence**: All incidents, audio transcripts, and rescued images are logged in a secure SQLite database.

### 🖥️ Modern Dashboard
- **Real-time Metrics**: Live websocket-based updates for all sensor data.
- **Active Defense UI**: Toggle on-the-fly correction modules like "Blur Fix" and "Glare Rescue".
- **Evidence Verification**: Integrated tool to upload and validate video clips for liveness and integrity.

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.9+**
- **Webcam** (Default Index: 0)
- **Tesseract OCR** (Optional, for text-based features)

### 2. Installation
```powershell
# Clone the repository
git clone https://github.com/ZeroDeaths7/AegisAI-tamper-resistent-surveillance-system.git
cd AegisAI-tamper-resistent-surveillance-system

# Set up virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the App
```powershell
python app.py
```
Open **[http://localhost:5000](http://localhost:5000)** in your browser.

---

## 🧠 Core Modules & Algorithms

<details>
<summary><b>1. Blur Detection & Correction</b></summary>

- **Detection**: Uses **Laplacian Variance Method** (`∇²I`). Sharp images have high variance (edges); blurry images have low variance as pixel intensity changes gradually.
- **Correction**: Applies an **Unsharp Mask** in real-time. 
  `Sharpened = Original + (Original - Blurred) × Strength`. 
  This amplifies high-frequency details (edges) to make the feed usable even during mild obstruction.
</details>

<details>
<summary><b>2. Shake & Reposition Detection</b></summary>

- **Algorithm**: **Farneback Dense Optical Flow**.
- **Shake**: Identifies high-magnitude, uniform motion across the entire frame (oscillatory patterns).
- **Repositioning**: Tracks directional consistency over multiple frames. If motion vectors point consistently in one direction (e.g., 90% alignment), a "Camera Moved" alert is triggered.
</details>

<details>
<summary><b>3. Glare Rescue (CLAHE)</b></summary>

- **Detection**: Histogram analysis identifies "blown out" highlights and "crushed" shadows.
- **Rescue**: Uses **Contrast Limited Adaptive Histogram Equalization (CLAHE)**. It divides the image into tiles, equalizes them locally to recover facial features or license plates from glare, and suppresses noise via contrast limiting.
</details>

<details>
<summary><b>4. Cryptographic Watermarking</b></summary>

- **Encoding**: Generates a unique **HMAC-SHA256** token using the current Unix timestamp and a secret key.
- **Embedding**: The first 3 bytes of the HMAC are converted into an RGB color, which is embedded as a 40x40 square in the frame.
- **Validation**: Uploaded videos are analyzed frame-by-frame. If the embedded colors don't match the expected HMACs for those timestamps, the video is flagged as a **Replay Attack**.
</details>

---

## 📁 Repository Structure

```text
aegisai/
├── app.py                # Main Flask-SocketIO server
├── backend/              # Core logic & algorithms
│   ├── tamper_detector.py
│   ├── glare_rescue.py
│   ├── database.py       # SQLite persistence
│   └── watermark_*.py    # Cryptographic modules
├── frontend/             # Dashboard (HTML/JS/CSS)
├── data/                 # Database and logs
├── storage/              # Evidence storage (glare pics, clips)
├── tests/                # Comprehensive test suite
├── scripts/              # Utility & legacy modules
└── assets/               # Demo samples and documentation assets
```

---

## ⚖️ License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ for secure, auditable environments.**
