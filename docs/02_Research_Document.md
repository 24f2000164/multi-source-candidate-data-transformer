# Candidate Data Transformer
### AI-Native Talent Intelligence – Research & Engineering Design Document v2.0

---

## Overview

The **Candidate Data Transformer** is a production-inspired CLI application that generates a standardized **Golden Candidate Record** from heterogeneous candidate data sources (ATS JSON + Resume PDF), ensuring deterministic processing, explainability, and extensibility.

This project implements the **foundational data integration layer** of an AI-Native Talent Intelligence Platform (inspired by Eightfold AI) — the clean canonical profile that powers downstream AI services like semantic search, candidate ranking, and interview agents.

---

## Problem Statement

Real-world hiring data comes from multiple sources with different schemas, duplicate values, conflicts, and missing fields. Raw candidate data cannot be directly used by AI systems. This transformer solves:

- **Data Heterogeneity** — Different schemas across ATS and Resume
- **Data Duplication** — Same candidate appearing multiple times
- **Data Inconsistency** — Conflicting values between sources
- **Missing Data** — Fields present in one source but not another
- **Data Quality Issues** — Invalid emails, phone formats, typos, date format differences

---

## Key Features

- Multi-source ingestion (ATS JSON + Resume PDF)
- Canonical Candidate Model (Golden Record)
- Rule-based deterministic merge engine
- Field-level provenance tracking
- Rule-based confidence scoring
- Three-stage validation (Input → Canonical → Output)
- Configurable output projection via YAML/JSON config
- Graceful error handling — never fails catastrophically

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.12+ |
| CLI | Typer |
| PDF Parsing | PyMuPDF (fitz) |
| Data Validation | Pydantic |
| Configuration | YAML / JSON |
| Testing | pytest |
| Logging | logging (stdlib) |
| Formatting | Ruff + Black |

---

## Architecture

The system follows a **Layered Pipeline Architecture**:

```
ATS JSON  ──┐
            ├──► Parser Layer
Resume PDF ─┘         │
                       ▼
              Canonical Candidate Model
                       │
                       ▼
                  Normalizer
                       │
                       ▼
                 Merge Engine
                       │
                       ▼
              Confidence Engine
                       │
                       ▼
                  Validation
                       │
                       ▼
              Projection Layer
                       │
                       ▼
           Golden Candidate Record (Output)
```

### Design Patterns Used

- **Strategy Pattern** — Parser selection
- **Factory Pattern** — Parser instantiation
- **Adapter Pattern** — Source schema mapping
- **SOLID Principles** — Throughout all components

---

## Canonical Candidate Schema

```
Candidate
├── candidate_id         : string
├── personal_information
│   ├── full_name        : string
│   ├── emails           : List<Email>
│   ├── phones           : List<Phone>
│   ├── location         : Address
│   └── links            : List<Link>
├── professional_information
│   ├── headline         : string
│   ├── current_company  : string
│   ├── years_of_experience : float
│   ├── skills           : List<Skill>
│   ├── experience       : List<Experience>
│   ├── education        : List<Education>
│   └── certifications   : List<Certification>
└── metadata
    ├── provenance
    ├── confidence
    ├── source_count
    └── generated_at
```

---

## Merge Policy

| Field | Rule |
|-------|------|
| Full Name | ATS wins (if valid and non-empty) |
| Email | ATS if valid, else Resume |
| Phone | ATS if valid, else Resume |
| Address | ATS wins |
| Skills | Union + Deduplicate |
| Experience | Resume wins (richer descriptions) |
| Education | Merge + Deduplicate |
| Certifications | Union |
| Links | Union |
| Headline | Resume if available |

Conflicts are recorded in **provenance** for full auditability.

---

## Confidence Scoring

| Scenario | Score |
|----------|-------|
| Present in ATS only (valid) | 0.85 |
| Present in Resume only | 0.70 |
| Present in both, values match | 0.98 |
| Conflict resolved using priority | 0.60 |
| Extracted with ambiguity | 0.50 |
| Invalid / Missing | 0.00 |

Overall confidence = weighted average across key fields (Name 20%, Email 15%, Phone 15%, Skills 15%, Experience 20%, Education 10%, Others 5%).

---

## Sample Input / Output

**ATS JSON Input:**
```json
{
  "candidateId": "ATS-1001",
  "fullName": "Sahil Kumar",
  "email": "sahil.kumar@gmail.com",
  "phone": "+919876543210",
  "skills": ["Python", "FastAPI", "Docker"]
}
```

**Resume (Parsed Output):**
```json
{
  "fullName": "Sahil R. Kumar",
  "skills": ["Python", "LangChain", "Docker"],
  "education": [
    { "college": "NIT Uttarakhand", "degree": "B.Tech" },
    { "college": "IIT Madras", "degree": "BS Data Science" }
  ]
}
```

**Golden Candidate Record:**
```json
{
  "candidate_id": "ATS-1001",
  "full_name": { "value": "Sahil Kumar", "confidence": 0.95, "provenance": ["ATS", "Resume"] },
  "emails": [{ "value": "sahil.kumar@gmail.com", "confidence": 0.98, "provenance": ["ATS", "Resume"] }],
  "skills": ["Python", "FastAPI", "Docker", "LangChain"],
  "overall_confidence": 0.91
}
```

---

## Configuration

**Default config:**
```yaml
projection:
  include:
    - full_name
    - emails
    - phones
    - skills
    - experience
    - education
confidence: true
provenance: true
```

**Custom config (minimal output):**
```yaml
projection:
  include:
    - full_name
    - emails
    - skills
confidence: false
provenance: false
```

---

## What This Project Does NOT Do

| Out of Scope | Responsibility |
|--------------|---------------|
| Job Recommendation | Future AI layer |
| Candidate Ranking | Future AI layer |
| Semantic Search | Future AI layer |
| Resume Scoring | Future AI layer |
| Interview Scheduling | Future AI layer |
| OCR / Scanned PDFs | Future enhancement |
| LinkedIn / GitHub parsing | Future enhancement |
| Batch processing | Future enhancement |

---

## Engineering Decisions

| ID | Decision |
|----|----------|
| ED-001 | Canonical Candidate Model as single internal representation |
| ED-002 | Rule-based deterministic Merge Policy |
| ED-003 | Rule-based Confidence Scoring (no ML/LLM) |
| ED-004 | Three-stage Validation Layer |
| ED-005 | Configuration-driven Projection |
| ED-006 | CLI as primary interface (Typer) |
| ED-007 | ATS JSON + Resume PDF as MVP input sources |
| ED-008 | Layered Pipeline Architecture |

---

## Success Criteria

- [x] ATS JSON parsed successfully
- [x] Resume PDF parsed successfully
- [x] Data transformed into Canonical Candidate Model
- [x] Merge rules applied deterministically
- [x] Conflicts resolved according to policy
- [x] Confidence scores generated
- [x] Provenance information preserved
- [x] Default and custom output projections work
- [x] Output passes schema validation
- [x] All unit and integration tests pass

---

## Assumptions

- ATS JSON is a trusted structured source
- Resume belongs to the same candidate as the ATS record
- Resume language is English
- Resume is machine-readable (no scanned OCR)
- Only one candidate is processed per execution
- Internet connectivity is not required

---

## Future Roadmap

- Recruiter CSV, GitHub, LinkedIn, Recruiter Notes ingestion
- Semantic Search + Embeddings + Vector Database
- Knowledge Graph integration
- LLM-based Resume Parser
- REST API interface
- Streamlit UI

---

## References

- [Eightfold AI Platform](https://eightfold.ai)
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io)
- [Pydantic Documentation](https://docs.pydantic.dev)
- [Typer Documentation](https://typer.tiangolo.com)
- [PyYAML Documentation](https://pyyaml.org/wiki/PyYAMLDocumentation)
- JSON Schema Specification
- RFC 5322 — Internet Message Format (Email)
- ITU-T E.164 Telephone Number Standard
- Master Data Management (MDM) Concepts

---

*Research Document v2.0 — Candidate Data Transformer*