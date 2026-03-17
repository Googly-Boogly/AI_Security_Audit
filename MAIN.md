# AI Security Audit Report

> **Classification:** `[CONFIDENTIAL / INTERNAL / PUBLIC]`
> **Version:** 1.0
> **Audit Date:** `[YYYY-MM-DD]`
> **Prepared By:** `[Auditor Name / Team]`
> **Reviewed By:** `[Reviewer Name]`
> **Organization:** `[Organization Name]`

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Audit Scope & Methodology](#2-audit-scope--methodology)
3. [System Architecture Overview](#3-system-architecture-overview)
4. [Threat Model](#4-threat-model)
5. [Findings & Vulnerabilities](#5-findings--vulnerabilities)
6. [Controls Assessment](#6-controls-assessment)
7. [Risk Register](#7-risk-register)
8. [Recommendations & Remediation Roadmap](#8-recommendations--remediation-roadmap)
9. [Appendices](#9-appendices)

---

## 1. Executive Summary

### 1.1 Purpose

This report documents the findings of a security audit conducted against `[System Name]`, an AI system operated by `[Organization Name]`. The audit assessed the system's exposure to AI-specific threats, infrastructure vulnerabilities, data handling risks, and alignment with industry security frameworks.

### 1.2 Audit Summary

| Attribute          | Detail                                              |
|--------------------|-----------------------------------------------------|
| System Audited     | `[System Name]`                                     |
| Audit Type         | AI Security / Red Team Assessment                   |
| Audit Period       | `[Start Date]` – `[End Date]`                       |
| Lead Auditor       | `[Name]`                                            |
| Frameworks Applied | OWASP LLM Top 10, MITRE ATLAS, NIST AI RMF          |

### 1.3 Key Findings Overview

| Severity    | Count |
|-------------|-------|
| 🔴 Critical  | `N`   |
| 🟠 High      | `N`   |
| 🟡 Medium    | `N`   |
| 🔵 Low       | `N`   |
| ℹ️ Info      | `N`   |

### 1.4 Overall Risk Posture

> `[One paragraph narrative for non-technical stakeholders. Describe the system's current security posture, the most significant risks identified, and the general urgency of remediation.]`

---

## 2. Audit Scope & Methodology

### 2.1 In Scope

- `[Component or surface area]`
- `[Component or surface area]`
- `[Component or surface area]`

### 2.2 Out of Scope

- `[Excluded component or surface area]`
- `[Excluded component or surface area]`

### 2.3 Methodology

> `[Describe the testing methodology: threat modeling approach, manual vs. automated testing, frameworks applied, any tools used.]`

### 2.4 Frameworks Reference

| Framework        | Version | Application                                       |
|------------------|---------|---------------------------------------------------|
| OWASP LLM Top 10 | `[ver]` | Vulnerability classification and test coverage    |
| MITRE ATLAS      | `[ver]` | Adversarial tactic and technique mapping          |
| NIST AI RMF      | `[ver]` | Governance, risk tolerance, and controls mapping  |

---

## 3. System Architecture Overview

### 3.1 System Description

> `[2–3 sentences describing the system's purpose, intended users, deployment environment, and key capabilities.]`

### 3.2 Component Inventory

| Component     | Technology / Provider | Role      |
|---------------|-----------------------|-----------|
| `[Component]` | `[Provider]`          | `[Role]`  |
| `[Component]` | `[Provider]`          | `[Role]`  |
| `[Component]` | `[Provider]`          | `[Role]`  |

### 3.3 Data Flow Summary

```
[Replace this block with a diagram or ASCII representation of the system data flow]

[User / External System]
        │
        ▼
[API Gateway + Auth Layer]
        │
        ▼
[Input Validation / Sanitization]
        │
        ▼
[Prompt Construction / RAG Retrieval]
        │
        ▼
[LLM Inference]
        │
        ▼
[Output Filtering / Guardrails]
        │
        ▼
[Response Delivery to User]
        │
        ▼
[Logging & Monitoring Layer]
```

### 3.4 Trust Boundaries

| Boundary      | Description                              |
|---------------|------------------------------------------|
| `[Boundary]`  | `[Trust level and enforcement notes]`    |
| `[Boundary]`  | `[Trust level and enforcement notes]`    |
| `[Boundary]`  | `[Trust level and enforcement notes]`    |

---

## 4. Threat Model

### 4.1 Protected Assets

| Asset     | Sensitivity | Description     |
|-----------|-------------|-----------------|
| `[Asset]` | `[Level]`   | `[Description]` |
| `[Asset]` | `[Level]`   | `[Description]` |
| `[Asset]` | `[Level]`   | `[Description]` |

### 4.2 Threat Actors

| Actor Type | Motivation     | Capability |
|------------|----------------|------------|
| `[Actor]`  | `[Motivation]` | `[Level]`  |
| `[Actor]`  | `[Motivation]` | `[Level]`  |
| `[Actor]`  | `[Motivation]` | `[Level]`  |

### 4.3 Attack Surface Map (MITRE ATLAS Aligned)

| Attack Surface | MITRE ATLAS Tactic | Technique          |
|----------------|--------------------|--------------------|
| `[Surface]`    | `[Tactic]`         | `[Technique + ID]` |
| `[Surface]`    | `[Tactic]`         | `[Technique + ID]` |
| `[Surface]`    | `[Tactic]`         | `[Technique + ID]` |

---

## 5. Findings & Vulnerabilities

> Each finding follows the format below. Duplicate the block for each finding. Group findings by category.
> **Categories:** Prompt Injection & Jailbreaking | Data Security | Model & Supply Chain Risk | Agentic & Multi-Agent Risks | Infrastructure & Deployment | Output Safety & Misuse

---

### Finding Template

#### FIND-000 — `[Finding Title]`

| Field           | Detail                                                            |
|-----------------|-------------------------------------------------------------------|
| **Severity**    | `[🔴 Critical / 🟠 High / 🟡 Medium / 🔵 Low / ℹ️ Info]`         |
| **OWASP Ref**   | `[e.g., LLM01: Prompt Injection]`                                 |
| **ATLAS Ref**   | `[e.g., AML.T0051]`                                               |
| **NIST AI RMF** | `[e.g., GOVERN 1.1, MAP 2.2]`                                     |

**Description:**
`[Describe the vulnerability, what conditions enable it, and what an attacker could achieve by exploiting it.]`

**Evidence / Test Case:**
```
Input / Payload:    [What was submitted]
Observed Behavior:  [What the system did]
Expected Behavior:  [What it should have done]
```

**Recommendation:**
`[Specific, actionable remediation steps.]`

---

## 6. Controls Assessment

| Control Domain             | Control Description | Status | Notes     |
|----------------------------|---------------------|--------|-----------|
| Input Validation           | `[Description]`     | `[ ]`  | `[Notes]` |
| Output Filtering           | `[Description]`     | `[ ]`  | `[Notes]` |
| Authentication             | `[Description]`     | `[ ]`  | `[Notes]` |
| Authorization              | `[Description]`     | `[ ]`  | `[Notes]` |
| Secrets Management         | `[Description]`     | `[ ]`  | `[Notes]` |
| Rate Limiting              | `[Description]`     | `[ ]`  | `[Notes]` |
| Data Encryption at Rest    | `[Description]`     | `[ ]`  | `[Notes]` |
| Data Encryption in Transit | `[Description]`     | `[ ]`  | `[Notes]` |
| Logging & Monitoring       | `[Description]`     | `[ ]`  | `[Notes]` |
| Supply Chain Verification  | `[Description]`     | `[ ]`  | `[Notes]` |
| Human-in-the-Loop          | `[Description]`     | `[ ]`  | `[Notes]` |
| Incident Response Plan     | `[Description]`     | `[ ]`  | `[Notes]` |

**Legend:** ✅ Present and Effective | ⚠️ Partial / Needs Improvement | ❌ Not Present

---

## 7. Risk Register

| ID       | Finding Title | Likelihood | Impact    | Risk Score | Owner     | Status |
|----------|---------------|------------|-----------|------------|-----------|--------|
| FIND-001 | `[Title]`     | `[Level]`  | `[Level]` | `[Score]`  | `[Team]`  | Open   |
| FIND-002 | `[Title]`     | `[Level]`  | `[Level]` | `[Score]`  | `[Team]`  | Open   |
| FIND-003 | `[Title]`     | `[Level]`  | `[Level]` | `[Score]`  | `[Team]`  | Open   |

---

## 8. Recommendations & Remediation Roadmap

### 8.1 Immediate (0–30 Days) — Critical Risk Reduction

| Priority | Action     | Addresses    |
|----------|------------|--------------|
| P0       | `[Action]` | `[FIND-XXX]` |
| P0       | `[Action]` | `[FIND-XXX]` |

### 8.2 Short-Term (30–90 Days) — High Risk Reduction

| Priority | Action     | Addresses    |
|----------|------------|--------------|
| P1       | `[Action]` | `[FIND-XXX]` |
| P1       | `[Action]` | `[FIND-XXX]` |

### 8.3 Medium-Term (90–180 Days) — Defense Depth & Governance

| Priority | Action     | Addresses    |
|----------|------------|--------------|
| P2       | `[Action]` | `[FIND-XXX]` |
| P3       | `[Action]` | `[FIND-XXX]` |

---

## 9. Appendices

### Appendix A — Test Cases & Payloads

> Restrict access to this appendix to authorized security personnel only.

| Test ID | Category     | Input / Payload | Expected Behavior | Observed Behavior |
|---------|--------------|-----------------|-------------------|-------------------|
| TC-001  | `[Category]` | `[Payload]`     | `[Expected]`      | `[Observed]`      |
| TC-002  | `[Category]` | `[Payload]`     | `[Expected]`      | `[Observed]`      |

---

### Appendix B — Framework Mappings

#### OWASP LLM Top 10 Coverage

| OWASP ID | Title                            | Findings Mapped |
|----------|----------------------------------|-----------------|
| LLM01    | Prompt Injection                 | `[FIND-XXX]`    |
| LLM02    | Insecure Output Handling         | `[FIND-XXX]`    |
| LLM03    | Training Data Poisoning          | `[FIND-XXX]`    |
| LLM04    | Model Denial of Service          | `[FIND-XXX]`    |
| LLM05    | Supply Chain Vulnerabilities     | `[FIND-XXX]`    |
| LLM06    | Sensitive Information Disclosure | `[FIND-XXX]`    |
| LLM07    | Insecure Plugin Design           | `[FIND-XXX]`    |
| LLM08    | Excessive Agency                 | `[FIND-XXX]`    |
| LLM09    | Overreliance                     | `[FIND-XXX]`    |
| LLM10    | Model Theft                      | `[FIND-XXX]`    |

#### MITRE ATLAS Coverage

| Tactic      | Technique          | Findings Mapped |
|-------------|--------------------|-----------------|
| `[Tactic]`  | `[Technique + ID]` | `[FIND-XXX]`    |
| `[Tactic]`  | `[Technique + ID]` | `[FIND-XXX]`    |

#### NIST AI RMF Function Mapping

| RMF Function | Category     | Findings Mapped |
|--------------|--------------|-----------------|
| GOVERN       | `[Category]` | `[FIND-XXX]`    |
| MAP          | `[Category]` | `[FIND-XXX]`    |
| MEASURE      | `[Category]` | `[FIND-XXX]`    |
| MANAGE       | `[Category]` | `[FIND-XXX]`    |

---

### Appendix C — Glossary

| Term                 | Definition |
|----------------------|------------|
| **Prompt Injection** | An attack where adversarial instructions are embedded in user input or retrieved content to manipulate model behavior. |
| **RAG**              | Retrieval-Augmented Generation — a technique combining a language model with a vector-based document retrieval system. |
| **Jailbreak**        | A technique to bypass an LLM's safety constraints and elicit policy-violating outputs. |
| **ATLAS**            | MITRE's Adversarial Threat Landscape for Artificial-Intelligence Systems — a knowledge base of adversarial ML tactics and techniques. |
| **OWASP LLM Top 10** | Open Worldwide Application Security Project's list of the top 10 security risks for LLM applications. |
| **NIST AI RMF**      | National Institute of Standards and Technology AI Risk Management Framework — a voluntary governance framework for managing AI risk. |
| **Excessive Agency** | An LLM vulnerability where the model is granted or assumes more permissions than necessary, enabling unintended or harmful actions. |
| **Least Privilege**  | A security principle where entities are granted only the minimum access rights necessary to perform their function. |
| **DPA**              | Data Processing Agreement — a contract governing how personal data is handled between a controller and processor. |

---

### Appendix D — References

- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [MITRE ATLAS](https://atlas.mitre.org/)
- [NIST AI Risk Management Framework 1.0](https://www.nist.gov/system/files/documents/2023/01/26/NIST.AI.100-1.pdf)
- [NIST AI 100-2: Adversarial Machine Learning](https://airc.nist.gov/Docs/2)
- [ENISA Threat Landscape for AI](https://www.enisa.europa.eu/publications/enisa-threat-landscape-for-ai)

---

*End of Report*

---
> **Document Control:** This document should be reviewed and updated after every major system change, at minimum annually, or following any AI security incident.
