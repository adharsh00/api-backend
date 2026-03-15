# Medical Image Validation Service

> **NCI Scalable Cloud Programming (H9SCPRO1) — CA Project**
> MSc Cloud Computing · National College of Ireland · Semester 2 2025–2026

A cloud-native, scalable medical image format validation service built with
**FastAPI**, **Vue.js 3**, **Amazon S3**, and **AWS SQS**, deployed on **EC2
(eu-west-1)**.

---

## Architecture

```
Browser → Vue.js (Nginx :80)
             │
             ▼
        FastAPI (:8000)
        ├── POST /validate-image  ← Custom API
        ├── /appointments/*       ← Classmate API proxy
        └── /public/*             ← file.io / ClinicalTrials proxy
             │
        ┌────┴────────┐
        │   AWS SQS   │ ← async validation queue
        └────┬────────┘
             │  (worker polls)
        ┌────▼────────┐
        │  Amazon S3  │ ← uploaded images
        └─────────────┘
```

---

## Project Structure

```
api-backend/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI entry point
│   │   ├── config.py             # Environment config
│   │   ├── routes/
│   │   │   ├── validation.py     # POST /validate-image, GET /formats
│   │   │   ├── appointments.py   # Proxy → classmate API
│   │   │   └── public_apis.py    # Proxy → file.io & ClinicalTrials
│   │   └── services/
│   │       ├── s3_service.py
│   │       ├── sqs_service.py
│   │       └── validation_service.py
│   ├── workers/
│   │   └── image_worker.py       # SQS consumer
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_validation.py
│   │   ├── test_appointments.py
│   │   ├── test_api.py
│   │   └── locustfile.py
│   ├── requirements.txt
│   └── pytest.ini
├── frontend/
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.js
│   │   ├── components/
│   │   │   ├── UploadImage.vue
│   │   │   ├── Appointments.vue
│   │   │   └── ClinicalTrials.vue
│   │   └── services/api.js
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── infra/
│   ├── create_security_group.py
│   ├── create_s3.py
│   ├── create_sqs.py
│   └── create_ec2.py
├── .github/workflows/deploy.yml
├── .env.example
└── README.md
```

---

## Quick Start — Local Development

### Backend

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
cd backend
pip install -r requirements.txt

# 3. Configure environment (S3/SQS calls are best-effort; API works without them)
cp ../.env.example ../.env
# Edit .env and fill in your AWS credentials

# 4. Start FastAPI (auto-reload)
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev          # Vite dev server on http://localhost:3000
```

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

### Load Testing (Locust)

```bash
locust -f tests/locustfile.py --host http://localhost:8000
# Open http://localhost:8089 in your browser
```

---

## AWS Infrastructure Setup

```bash
# 1. Create S3 bucket
python infra/create_s3.py

# 2. Create SQS queue
python infra/create_sqs.py

# 3. Create security group (provide your VPC ID)
python infra/create_security_group.py <vpc-id>

# 4. Launch EC2 instance (provide the security group ID from step 3)
python infra/create_ec2.py <sg-id>
```

---

## EC2 Deployment (Manual)

```bash
ssh -i cloud-key-pair.pem ec2-user@<PUBLIC-IP>
cd /home/ec2-user/api-backend

# Set environment variables
cp .env.example .env && nano .env

# Start services
sudo systemctl start api worker nginx
```

---

## APIs Integrated

| Service | Type | Purpose |
|---------|------|---------|
| `/validate-image` | Custom | MIME detection & format validation |
| Healthcare Appointment API | Classmate | Slot booking & reservations |
| [file.io](https://file.io) | Public | Pre-upload MIME type detection |
| [ClinicalTrials.gov](https://clinicaltrials.gov/api/v2) | Public | Medical study search |

---

## Security Notes

- AWS credentials are loaded from environment variables — **never hard-coded**
- `.env` is git-ignored; use `.env.example` as a template
- S3 bucket has all public access blocked
- File uploads are size-limited and filename-sanitised
- CORS is restricted to the frontend domain in production

---

## GitHub Actions CI/CD

Push to `main` triggers:
1. Unit tests via `pytest`
2. SSH deploy to EC2 (git pull → restart services → rebuild frontend)

Set the following repository secrets in **Settings → Secrets → Actions**:

| Secret | Value |
|--------|-------|
| `EC2_HOST` | EC2 public IP |
| `EC2_SSH_KEY` | Contents of `cloud-key-pair.pem` |
| `AWS_ACCESS_KEY_ID` | IAM access key |
| `AWS_SECRET_ACCESS_KEY` | IAM secret key |
| `S3_BUCKET_NAME` | `medical-image-validation` |
| `SQS_QUEUE_URL` | Full SQS queue URL |
