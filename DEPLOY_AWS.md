# AWS Deployment Guide — Project 13 Resume Parsing + Candidate Ranking

---

## AWS Services for Resume Parsing & Candidate Ranking

### 1. Ready-to-Use AI (No Model Needed)

| Service                    | What it does                                                                 | When to use                                        |
|----------------------------|------------------------------------------------------------------------------|----------------------------------------------------|
| **Amazon Textract**        | Extract text, tables, and key-value pairs from PDF/DOCX resumes              | Replace your PyMuPDF + python-docx pipeline        |
| **Amazon Comprehend**      | NER for PERSON, ORG, DATE entities from extracted resume text                | Replace your spaCy NER pipeline                    |
| **Amazon Bedrock**         | Claude/Titan for semantic candidate ranking and structured extraction        | Replace your sentence-transformers ranking         |

> **Amazon Textract + Comprehend** replace your PyMuPDF + spaCy pipeline. For ranking, **Amazon Bedrock** can score candidates against a job description with a single prompt.

### 2. Host Your Own Model (Keep Current Stack)

| Service                    | What it does                                                        | When to use                                           |
|----------------------------|---------------------------------------------------------------------|-------------------------------------------------------|
| **AWS App Runner**         | Run backend container — simplest, no VPC or cluster needed          | Quickest path to production                           |
| **Amazon ECS Fargate**     | Run backend + nlp-service containers in a private VPC               | Best match for your current microservice architecture |
| **Amazon ECR**             | Store your Docker images                                            | Used with App Runner, ECS, or EKS                     |

### 3. Supporting Services

| Service                  | Purpose                                                                   |
|--------------------------|---------------------------------------------------------------------------|
| **Amazon S3**            | Store uploaded resume files and parsed JSON results                       |
| **AWS Secrets Manager**  | Store API keys and connection strings instead of .env files               |
| **Amazon CloudWatch**    | Track parsing latency, ranking scores, request volume                     |

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  S3 + CloudFront — React Frontend                           │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│  AWS App Runner / ECS Fargate — Backend (FastAPI :8000)     │
└──────────────────────┬──────────────────────────────────────┘
                       │ Internal
        ┌──────────────┴──────────────┐
        │ Option A                    │ Option B
        ▼                             ▼
┌───────────────────┐    ┌────────────────────────────────────┐
│ ECS Fargate       │    │ Amazon Textract + Comprehend       │
│ NLP Service :8001 │    │ + Amazon Bedrock (ranking)         │
│ spaCy+sentence-   │    │ No model maintenance needed        │
│ transformers      │    │                                    │
└───────────────────┘    └────────────────────────────────────┘
```

---

## Prerequisites

```bash
aws configure
AWS_REGION=eu-west-2
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
```

---

## Step 1 — Create ECR and Push Images

```bash
aws ecr create-repository --repository-name candidateranking/nlp-service --region $AWS_REGION
aws ecr create-repository --repository-name candidateranking/backend --region $AWS_REGION
ECR=$AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR
docker build -f docker/Dockerfile.nlp-service -t $ECR/candidateranking/nlp-service:latest ./nlp-service
docker push $ECR/candidateranking/nlp-service:latest
docker build -f docker/Dockerfile.backend -t $ECR/candidateranking/backend:latest ./backend
docker push $ECR/candidateranking/backend:latest
```

---

## Step 2 — Create S3 Bucket for Resumes

```bash
aws s3 mb s3://candidate-resumes-$AWS_ACCOUNT --region $AWS_REGION
```

---

## Step 3 — Deploy with App Runner

```bash
aws apprunner create-service \
  --service-name candidateranking-backend \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "'$ECR'/candidateranking/backend:latest",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {
        "Port": "8000",
        "RuntimeEnvironmentVariables": {
          "NLP_SERVICE_URL": "http://nlp-service:8001"
        }
      }
    }
  }' \
  --instance-configuration '{"Cpu": "1 vCPU", "Memory": "2 GB"}' \
  --region $AWS_REGION
```

---

## Option B — Use Amazon Textract + Comprehend + Bedrock

```python
import boto3, json

textract = boto3.client("textract", region_name="eu-west-2")
comprehend = boto3.client("comprehend", region_name="eu-west-2")
bedrock = boto3.client("bedrock-runtime", region_name="eu-west-2")

def parse_and_rank(resume_bytes: bytes, job_description: str) -> dict:
    # Extract text
    text_response = textract.detect_document_text(Document={"Bytes": resume_bytes})
    resume_text = " ".join([b["Text"] for b in text_response["Blocks"] if b["BlockType"] == "LINE"])
    # Extract entities
    entities = comprehend.detect_entities(Text=resume_text[:5000], LanguageCode="en")
    # Rank against JD
    prompt = f"Score this resume (0-100) against the job description.\nJD: {job_description}\nResume: {resume_text[:3000]}\nReturn JSON: {{score, reasoning}}"
    response = bedrock.invoke_model(
        modelId="anthropic.claude-v2",
        body=json.dumps({"prompt": prompt, "max_tokens_to_sample": 300}),
        contentType="application/json"
    )
    ranking = json.loads(json.loads(response["body"].read())["completion"])
    return {"entities": entities["Entities"], "ranking": ranking}
```

---

## Estimated Monthly Cost

| Service                    | Tier              | Est. Cost          |
|----------------------------|-------------------|--------------------|
| App Runner (backend)       | 1 vCPU / 2 GB     | ~$20–25/month      |
| App Runner (nlp-service)   | 1 vCPU / 2 GB     | ~$20–25/month      |
| ECR + S3 + CloudFront      | Standard          | ~$3–7/month        |
| Amazon Textract            | Pay per page      | ~$1.50/1000 pages  |
| Amazon Bedrock             | Pay per token     | ~$5–10/month       |
| **Total (Option A)**       |                   | **~$43–57/month**  |
| **Total (Option B)**       |                   | **~$28–42/month**  |

For exact estimates → https://calculator.aws

---

## Teardown

```bash
aws ecr delete-repository --repository-name candidateranking/backend --force
aws ecr delete-repository --repository-name candidateranking/nlp-service --force
aws s3 rm s3://candidate-resumes-$AWS_ACCOUNT --recursive
aws s3 rb s3://candidate-resumes-$AWS_ACCOUNT
```
