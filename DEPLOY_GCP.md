# GCP Deployment Guide — Project 13 Resume Parsing + Candidate Ranking

---

## GCP Services for Resume Parsing & Candidate Ranking

### 1. Ready-to-Use AI (No Model Needed)

| Service                              | What it does                                                                 | When to use                                        |
|--------------------------------------|------------------------------------------------------------------------------|----------------------------------------------------|
| **Cloud Document AI**                | Extract structured data from PDF/DOCX resumes — name, email, skills, dates  | Replace your PyMuPDF + spaCy pipeline              |
| **Cloud Natural Language API**       | NER for PERSON, ORG, DATE entities from extracted resume text                | Replace your spaCy NER pipeline                    |
| **Vertex AI Gemini**                 | Gemini Pro for semantic candidate ranking against a job description          | Replace your sentence-transformers ranking         |

> **Cloud Document AI + Vertex AI Gemini** replace your PyMuPDF + spaCy + sentence-transformers pipeline with managed services.

### 2. Host Your Own Model (Keep Current Stack)

| Service                    | What it does                                                        | When to use                                           |
|----------------------------|---------------------------------------------------------------------|-------------------------------------------------------|
| **Cloud Run**              | Run backend + nlp-service containers — serverless, scales to zero   | Best match for your current microservice architecture |
| **Artifact Registry**      | Store your Docker images                                            | Used with Cloud Run or GKE                            |

### 3. Supporting Services

| Service                        | Purpose                                                                   |
|--------------------------------|---------------------------------------------------------------------------|
| **Cloud Storage**              | Store uploaded resume files and parsed JSON results                       |
| **Secret Manager**             | Store API keys and connection strings instead of .env files               |
| **Cloud Monitoring + Logging** | Track parsing latency, ranking scores, request volume                     |

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Firebase Hosting — React Frontend                          │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│  Cloud Run — Backend (FastAPI :8000)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ Internal HTTPS
        ┌──────────────┴──────────────┐
        │ Option A                    │ Option B
        ▼                             ▼
┌───────────────────┐    ┌────────────────────────────────────┐
│ Cloud Run         │    │ Cloud Document AI                  │
│ NLP Service :8001 │    │ + Vertex AI Gemini (ranking)       │
│ spaCy+sentence-   │    │ No model maintenance needed        │
│ transformers      │    │                                    │
└───────────────────┘    └────────────────────────────────────┘
```

---

## Prerequisites

```bash
gcloud auth login
gcloud projects create candidateranking-project --name="Candidate Ranking"
gcloud config set project candidateranking-project
gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com language.googleapis.com \
  documentai.googleapis.com aiplatform.googleapis.com \
  storage.googleapis.com cloudbuild.googleapis.com
```

---

## Step 1 — Create Artifact Registry and Push Images

```bash
GCP_REGION=europe-west2
gcloud artifacts repositories create candidateranking-repo \
  --repository-format=docker --location=$GCP_REGION
gcloud auth configure-docker $GCP_REGION-docker.pkg.dev
AR=$GCP_REGION-docker.pkg.dev/candidateranking-project/candidateranking-repo
docker build -f docker/Dockerfile.nlp-service -t $AR/nlp-service:latest ./nlp-service
docker push $AR/nlp-service:latest
docker build -f docker/Dockerfile.backend -t $AR/backend:latest ./backend
docker push $AR/backend:latest
```

---

## Step 2 — Deploy to Cloud Run

```bash
gcloud run deploy nlp-service \
  --image $AR/nlp-service:latest --region $GCP_REGION \
  --port 8001 --no-allow-unauthenticated \
  --min-instances 1 --max-instances 3 --memory 2Gi --cpu 1

NLP_URL=$(gcloud run services describe nlp-service --region $GCP_REGION --format "value(status.url)")

gcloud run deploy backend \
  --image $AR/backend:latest --region $GCP_REGION \
  --port 8000 --allow-unauthenticated \
  --min-instances 1 --max-instances 5 --memory 1Gi --cpu 1 \
  --set-env-vars NLP_SERVICE_URL=$NLP_URL
```

---

## Option B — Use Cloud Document AI + Vertex AI Gemini

```python
from google.cloud import documentai_v1 as documentai
import vertexai
from vertexai.generative_models import GenerativeModel

vertexai.init(project="candidateranking-project", location="europe-west2")
gemini = GenerativeModel("gemini-pro")
doc_client = documentai.DocumentProcessorServiceClient()

def parse_and_rank(file_bytes: bytes, job_description: str) -> dict:
    processor_name = "projects/candidateranking-project/locations/eu/processors/<processor-id>"
    raw_document = documentai.RawDocument(content=file_bytes, mime_type="application/pdf")
    result = doc_client.process_document(
        request=documentai.ProcessRequest(name=processor_name, raw_document=raw_document)
    )
    resume_text = result.document.text
    response = gemini.generate_content(
        f"Score this resume (0-100) against the JD.\nJD: {job_description}\nResume: {resume_text[:3000]}\nReturn JSON: {{score, reasoning, skills_match}}"
    )
    import json
    ranking = json.loads(response.text)
    return {"resume_text": resume_text, "ranking": ranking}
```

---

## Estimated Monthly Cost

| Service                    | Tier                  | Est. Cost          |
|----------------------------|-----------------------|--------------------|
| Cloud Run (backend)        | 1 vCPU / 1 GB         | ~$10–15/month      |
| Cloud Run (nlp-service)    | 1 vCPU / 2 GB         | ~$12–18/month      |
| Artifact Registry          | Storage               | ~$1–2/month        |
| Firebase Hosting           | Free tier             | $0                 |
| Cloud Document AI          | Pay per page          | ~$1.50/1000 pages  |
| Vertex AI Gemini           | Pay per token         | ~$3–8/month        |
| **Total (Option A)**       |                       | **~$23–35/month**  |
| **Total (Option B)**       |                       | **~$15–25/month**  |

For exact estimates → https://cloud.google.com/products/calculator

---

## Teardown

```bash
gcloud run services delete backend --region $GCP_REGION --quiet
gcloud run services delete nlp-service --region $GCP_REGION --quiet
gcloud artifacts repositories delete candidateranking-repo --location=$GCP_REGION --quiet
gcloud projects delete candidateranking-project
```
