# AI Security Audit Template

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-1.0.0-green.svg)
![Frameworks](https://img.shields.io/badge/frameworks-OWASP%20LLM%20%7C%20MITRE%20ATLAS%20%7C%20NIST%20AI%20RMF-orange.svg)
![Status](https://img.shields.io/badge/status-active-brightgreen.svg)

A professional, framework-aligned security audit template for AI and LLM-based systems. Designed to be reusable across engagements, this template provides a structured approach to identifying, documenting, and remediating AI-specific security risks.

---

## About

AI systems introduce a distinct class of security risks that traditional audit frameworks don't fully address — prompt injection, RAG poisoning, excessive agency, supply chain compromise, and more. This template bridges that gap by mapping findings directly to the three leading AI security frameworks:

- **[OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)** — Vulnerability classification
- **[MITRE ATLAS](https://atlas.mitre.org/)** — Adversarial tactic and technique mapping
- **[NIST AI RMF 1.0](https://www.nist.gov/system/files/documents/2023/01/26/NIST.AI.100-1.pdf)** — Governance and risk management alignment

Built by [Sophie](https://github.com/[your-handle]) — AI Engineer and Security Researcher specializing in multi-agent systems and AI security architecture.

---

## What's Inside

```
ai-security-audit-template/
└── ai_security_audit_template.md   # The full audit template
```

The template covers:

- **Executive Summary** — Risk posture narrative and findings overview for stakeholders
- **Scope & Methodology** — In-scope systems, exclusions, and testing approach
- **System Architecture Overview** — Component inventory, data flow, and trust boundaries
- **Threat Model** — Protected assets, threat actors, and ATLAS-aligned attack surface map
- **Findings & Vulnerabilities** — Structured finding blocks across 6 risk categories
- **Controls Assessment** — 12-domain control evaluation with status tracking
- **Risk Register** — Prioritized finding table with likelihood × impact scoring
- **Remediation Roadmap** — Phased action plan (0–30, 30–90, 90–180 days)
- **Appendices** — Test cases, full framework cross-mapping tables, glossary, and references

---

## Quickstart

### 1. Clone or download the template

```bash
git clone https://github.com/[your-handle]/ai-security-audit-template.git
cd ai-security-audit-template
```

### 2. Open the template

The audit lives in a single Markdown file:

```bash
# Open in your editor of choice
code ai_security_audit_template.md
```

### 3. Fill in the header metadata

At the top of the file, update the classification, version, audit date, auditor name, and organization:

```markdown
> **Classification:** CONFIDENTIAL
> **Version:** 1.0
> **Audit Date:** 2025-06-01
> **Prepared By:** Sophie
> **Organization:** Acme Corp
```

### 4. Complete each section

Work through the document top to bottom. Every field marked with `[brackets]` is a placeholder for your content. Key sections to prioritize:

| Section | What to fill in |
|---|---|
| Executive Summary | Risk posture narrative, finding counts |
| System Architecture | Component inventory, data flow diagram |
| Threat Model | Assets, actors, attack surface |
| Findings | One block per finding — duplicate the template block as needed |
| Controls Assessment | Status (✅ / ⚠️ / ❌) and notes per control domain |
| Risk Register | Populate as findings are written |
| Remediation Roadmap | Assign actions to findings and owners |
| Appendix B | Map each finding to OWASP, ATLAS, and NIST RMF IDs |

### 5. Export (optional)

Convert to PDF or Word using [Pandoc](https://pandoc.org/):

```bash
# PDF
pandoc ai_security_audit_template.md -o audit_report.pdf

# Word (.docx)
pandoc ai_security_audit_template.md -o audit_report.docx
```

---

## Finding Severity Reference

| Severity    | Description                                            |
|-------------|--------------------------------------------------------|
| 🔴 Critical  | Immediate exploitation risk; remediate within 24–72hrs |
| 🟠 High      | Significant risk; remediate within 30 days             |
| 🟡 Medium    | Moderate risk; remediate within 90 days                |
| 🔵 Low       | Minor risk; address in next review cycle               |
| ℹ️ Info      | Informational; no immediate action required            |

---

## Vulnerability Categories Covered

| Category                      | Example Risks                                             |
|-------------------------------|-----------------------------------------------------------|
| Prompt Injection & Jailbreaking | Direct injection, indirect RAG injection, jailbreaks    |
| Data Security                 | PII leakage, unencrypted vector stores, context exposure |
| Model & Supply Chain Risk     | Unverified providers, unpinned dependencies, data poisoning |
| Agentic & Multi-Agent Risks   | Excessive tool permissions, inter-agent prompt injection  |
| Infrastructure & Deployment   | Secrets mismanagement, missing rate limiting             |
| Output Safety & Misuse        | Missing content filters, harmful output surfacing        |

---

## License

This project is licensed under the [MIT License](LICENSE).

---

*Built with a blue team mindset. Use responsibly and only on systems you are authorized to audit.*
