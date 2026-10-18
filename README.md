# IDShield AI — Intelligent Identity & Document Screening Platform

IDShield AI is an enterprise-grade, secure, modular, and explainable AI-assisted identity document screening, digital forensics, and OSINT investigation platform designed for border security, immigration authorities, and document verification units.

---

## 1. System Architecture & Key Capabilities

- **Optical Character Recognition (OCR) Engine**: Automatic classification and field extraction for ICAO Doc 9303 passports, Schengen/international visas, and national identity cards with per-field confidence scoring and operator correction workflows.
- **ICAO Checksum & Rule-Based Validation**: Deterministic validation verifying 7-3-1 weighting checksums, expiration boundaries, chronological issue/expiry alignment, holder age sanity, and MRZ-to-visual consistency.
- **AI-Assisted Document Tampering & Digital Forensics Pipeline**:
  - **Error Level Analysis (ELA)**: Detects compression variance indicating image compositing, cloned layers, and digital manipulation.
  - **Portrait Boundary Seam Analysis**: Detects sharp edge discontinuities and spliced laminate boundaries indicative of photograph replacement.
  - **Typography & Font Kerning Inconsistency**: Detects character alignment jitter and font substitutions.
  - **EXIF Metadata Forensics**: Flags image-editing software footprints (Photoshop, GIMP, Canva).
- **Authorized 1:1 Facial Biometric Comparison**: Face detection and feature correlation matching document portraiture with live presentation probes under supervisory audit controls.
- **Extensible OSINT Framework**: Pluggable connectors for **SpiderFoot**, **theHarvester**, **Maltego Transform Hub**, and **OpenSanctions / Public Watchlists** with complete source attribution, reliability ratings, and evidence links.
- **Authorized Database Verification**: Direct adapters for **INTERPOL Stolen & Lost Travel Documents (SLTD)**, **National Visa Verification Gateways**, and revocation registers (with clearly labeled mock and live modes).
- **Transparent Explainable Risk Engine**: Quantifiable scoring from 0 to 100 with granular factor weighting, evidence pointers, and zero blind penalty for missing optional records.
- **Audit Logging & Case Adjudication**: Immutable audit trails recording every actor, action, IP, and outcome; official downloadable tamper-evident PDF screening reports.

---

## 2. Directory Layout

```
idshield-ai/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI REST endpoints (auth, documents, cases, dashboard)
│   │   ├── core/         # Config, security, DB engine & initial seed data
│   │   ├── models/       # SQLAlchemy async relational ORM models
│   │   ├── schemas/      # Pydantic request/response validation schemas
│   │   ├── services/     # OCR, Forensics, Face, OSINT, DB verify, Risk & PDF engines
│   │   └── tests/        # Automated integration and unit tests (pytest / anyio)
│   ├── storage/          # Protected uploaded docs, samples & generated PDF reports
│   └── requirements.txt  # Pinned backend dependencies
├── frontend/
│   ├── src/
│   │   ├── api/          # Axios HTTP client with JWT interceptor
│   │   ├── components/   # Sidebar, visual overlays, modals
│   │   ├── pages/        # Dashboard, Screening, Cases, Detail, OSINT, Audit, Login
│   │   └── types/        # Full TypeScript domain contracts
│   ├── tailwind.config.js# Security-grade dark navy theme configuration
│   └── package.json
├── docker-compose.yml    # Containerized multi-service deployment
├── Dockerfile.backend    # Python 3.12 + OpenCV headless runtime
├── Dockerfile.frontend   # Node.js builder + Nginx edge server
└── .env.example          # Environment variables template
```

---

## 3. Quick Start & Local Run Instructions

### Prerequisites
- Python 3.12+ (or `uv`)
- Node.js 18+ and `npm`

### Step 1: Start Backend API
```powershell
cd backend
# Create virtual environment if needed:
# uv venv .venv --python python3.12
# .venv\Scripts\activate
# uv pip install -r requirements.txt

# Start uvicorn server:
..\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload
```
*The database and synthetic test specimens (`passport_alexander_morgan.jpg`, `passport_altered_tampered.jpg`) will automatically initialize on first launch.*

- **Backend API & Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

### Step 2: Start Frontend Web Application
```powershell
cd frontend
npm install
npm run dev
```
- **Web Terminal**: [http://localhost:5173](http://localhost:5173)

---

## 4. Test Credentials & Demo Accounts

| Role | Username | Password | Permitted Capabilities |
| :--- | :--- | :--- | :--- |
| **Border Officer** | `officer` | `Officer@123456` | Ingest documents, review OCR, run validation, adjudicate cases |
| **OSINT Analyst** | `investigator` | `Investigator@123` | Execute OSINT queries, map relationships, corroborate findings |
| **Supervisor** | `supervisor` | `Supervisor@123` | Inspect overrides, approve high-risk escalations, metrics review |
| **System Admin** | `admin` | `Admin@123456` | System configuration, integration status, audit trail inspection |

---

## 5. Automated Test Execution

Run the backend test suite:
```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest app/tests -p no:asyncio -v
```

---

## 6. Security, Privacy & Ethical Compliance

1. **Human-in-the-Loop Safeguard**: Automated risk scores and forensic findings are advisory indicators designed solely to assist human officers. No consequential border or legal decision can be triggered automatically.
2. **Biometric Privacy Minimization**: Facial comparison operates only for authorized 1:1 verification. Facial templates are ephemeral and non-reconstructible.
3. **Evidence Integrity**: Every uploaded credential is cryptographically hashed with SHA-256 upon ingestion and recorded in an immutable audit ledger.
4. **Mock vs Production Transparency**: External database queries and unconfigured third-party tools are explicitly flagged with status badges (`Operational`, `Mock Gateway`, or `Awaiting Configuration`).

---

## 7. Deploy on Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/PramodTewatia2007/idshield-ai)

IDShield AI comes with a turnkey Render Blueprint (`render.yaml`) that builds the React frontend and runs the FastAPI backend in a unified, production-ready web service on Render's Free tier.

### Option A: One-Click Blueprint Deployment (Recommended)

1. Click the **Deploy to Render** button above (or visit [https://dashboard.render.com/blueprints/new](https://dashboard.render.com/blueprints/new)).
2. Connect your GitHub repository: `PramodTewatia2007/idshield-ai`.
3. Render will automatically detect `render.yaml` and configure:
   - **Service Name**: `idshield-ai`
   - **Environment**: Python 3.11
   - **Build Command**: `bash ./build.sh` (installs node dependencies, builds frontend, installs python packages)
   - **Start Command**: `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`
4. Click **Apply**. Within ~2-3 minutes, your live application URL (e.g. `https://idshield-ai.onrender.com`) will be active with both the UI and API fully functional!

### Option B: Manual Web Service Setup in Render Dashboard

If you prefer to configure manually without the Blueprint:

1. In the [Render Dashboard](https://dashboard.render.com/), click **New +** -> **Web Service**.
2. Connect your repository: `PramodTewatia2007/idshield-ai`.
3. Fill in the service configuration:
   - **Name**: `idshield-ai`
   - **Language / Runtime**: `Python 3`
   - **Branch**: `main`
   - **Region**: Any (e.g., *Oregon (US West)* or *Frankfurt (EU)*)
   - **Build Command**: `bash ./build.sh`
   - **Start Command**: `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`
4. In **Advanced Settings**, add the following **Environment Variables**:
   | Key | Value | Description |
   | :--- | :--- | :--- |
   | `PYTHON_VERSION` | `3.11.9` | Sets the Python runtime version |
   | `NODE_VERSION` | `20` | Node.js version for frontend build |
   | `SECRET_KEY` | *(Click "Generate")* | Cryptographic signing key for JWTs |
   | `DATABASE_URL` | `sqlite+aiosqlite:///./idshield.db` | Default database connection |
   | `DEMO_MODE` | `true` | Pre-seeds demo border cases & documents |
   | `CORS_ORIGINS` | `*` | Allowed CORS origins |
5. Set **Health Check Path** to `/health`.
6. Click **Create Web Service**. Render will execute `build.sh` and launch the app.

