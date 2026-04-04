# Azure Deployment Guide — Project 13 Resume Parsing + Candidate Ranking

---

## Azure Services for Resume Parsing & Candidate Ranking

### 1. Ready-to-Use AI (No Model Needed)

| Service                              | What it does                                                                 | When to use                                        |
|--------------------------------------|------------------------------------------------------------------------------|----------------------------------------------------|
| **Azure AI Document Intelligence**   | Extract structured data from PDF/DOCX resumes — name, email, skills, dates  | Replace your PyMuPDF + spaCy pipeline              |
| **Azure AI Language — Custom NER**   | Train custom entities for resume-specific fields                             | When you need domain-specific entity extraction    |
| **Azure OpenAI Service**             | GPT-4 for semantic candidate ranking against a job description               | Replace your sentence-transformers ranking         |

> **Azure AI Document Intelligence + Azure OpenAI** replace your PyMuPDF + spaCy + sentence-transformers pipeline with managed services.

### 2. Host Your Own Model (Keep Current Stack)

| Service                        | What it does                                                        | When to use                                           |
|--------------------------------|---------------------------------------------------------------------|-------------------------------------------------------|
| **Azure Container Apps**       | Run your 3 Docker containers (frontend, backend, nlp-service)       | Best match for your current microservice architecture |
| **Azure Container Registry**   | Store your Docker images                                            | Used with Container Apps or AKS                       |

### 3. Supporting Services

| Service                       | Purpose                                                                  |
|-------------------------------|--------------------------------------------------------------------------|
| **Azure Blob Storage**        | Store uploaded resume files and parsed JSON results                      |
| **Azure Key Vault**           | Store API keys and connection strings instead of .env files              |
| **Azure Monitor + App Insights** | Track parsing latency, ranking scores, request volume                |

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Azure Static Web Apps — React Frontend                     │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│  Azure Container Apps — Backend (FastAPI :8000)             │
└──────────────────────┬──────────────────────────────────────┘
                       │ Internal
        ┌──────────────┴──────────────┐
        │ Option A                    │ Option B
        ▼                             ▼
┌───────────────────┐    ┌────────────────────────────────────┐
│ Container Apps    │    │ Azure AI Document Intelligence     │
│ NLP Service :8001 │    │ + Azure OpenAI (ranking)           │
│ spaCy+sentence-   │    │ No model maintenance needed        │
│ transformers      │    │                                    │
└───────────────────┘    └────────────────────────────────────┘
```

---

## Prerequisites

```bash
az login
az group create --name rg-candidate-ranking --location uksouth
az extension add --name containerapp --upgrade
```

---

## Step 1 — Create Container Registry and Push Images

```bash
az acr create --resource-group rg-candidate-ranking --name candidaterankingacr --sku Basic --admin-enabled true
az acr login --name candidaterankingacr
ACR=candidaterankingacr.azurecr.io
docker build -f docker/Dockerfile.nlp-service -t $ACR/nlp-service:latest ./nlp-service
docker push $ACR/nlp-service:latest
docker build -f docker/Dockerfile.backend -t $ACR/backend:latest ./backend
docker push $ACR/backend:latest
```

---

## Step 2 — Create Blob Storage for Resumes

```bash
az storage account create --name candidateresumes --resource-group rg-candidate-ranking --sku Standard_LRS
az storage container create --name resumes --account-name candidateresumes
az storage container create --name parsed --account-name candidateresumes
```

---

## Step 3 — Deploy Container Apps

```bash
az containerapp env create --name candidateranking-env --resource-group rg-candidate-ranking --location uksouth

az containerapp create \
  --name nlp-service --resource-group rg-candidate-ranking \
  --environment candidateranking-env --image $ACR/nlp-service:latest \
  --registry-server $ACR --target-port 8001 --ingress internal \
  --min-replicas 1 --max-replicas 3 --cpu 1 --memory 2.0Gi

az containerapp create \
  --name backend --resource-group rg-candidate-ranking \
  --environment candidateranking-env --image $ACR/backend:latest \
  --registry-server $ACR --target-port 8000 --ingress external \
  --min-replicas 1 --max-replicas 5 --cpu 0.5 --memory 1.0Gi \
  --env-vars NLP_SERVICE_URL=http://nlp-service:8001
```

---

## Option B — Use Azure AI Document Intelligence + Azure OpenAI

```python
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI

doc_client = DocumentAnalysisClient(
    endpoint=os.getenv("AZURE_DOC_INTELLIGENCE_ENDPOINT"),
    credential=AzureKeyCredential(os.getenv("AZURE_DOC_INTELLIGENCE_KEY"))
)
openai_client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-02-01"
)

def parse_and_rank(file_bytes: bytes, job_description: str) -> dict:
    poller = doc_client.begin_analyze_document("prebuilt-document", file_bytes)
    result = poller.result()
    resume_text = result.content
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": f"Score this resume (0-100) against the JD.\nJD: {job_description}\nResume: {resume_text[:3000]}\nReturn JSON: {{score, reasoning, skills_match}}"}]
    )
    import json
    ranking = json.loads(response.choices[0].message.content)
    return {"resume_text": resume_text, "ranking": ranking}
```

---

## Estimated Monthly Cost

| Service                  | Tier      | Est. Cost         |
|--------------------------|-----------|-------------------|
| Container Apps (backend) | 0.5 vCPU  | ~$10–15/month     |
| Container Apps (nlp-svc) | 1 vCPU    | ~$15–20/month     |
| Container Registry       | Basic     | ~$5/month         |
| Static Web Apps          | Free      | $0                |
| Doc Intelligence         | S0 tier   | Pay per page      |
| Azure OpenAI (GPT-4)     | Pay per token | ~$5–15/month  |
| **Total (Option A)**     |           | **~$30–40/month** |
| **Total (Option B)**     |           | **~$20–35/month** |

For exact estimates → https://calculator.azure.com

---

## Teardown

```bash
az group delete --name rg-candidate-ranking --yes --no-wait
```
