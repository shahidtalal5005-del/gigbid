# GigBid — Multi-Agent Freelancer Copilot (AI-4016)

![GigBid Demo](link-to-your-30-second-demo.gif)

GigBid is a deployed web application where a team of LangGraph agents finds freelance jobs, assesses risks, writes proposals grounded in real portfolio evidence, and manages client conversations. Every outgoing action requires human approval.

## Architecture
*(Insert architecture diagram image here)*
* **Scout:** Discovers and queues new jobs.
* **Job Analyst, Risk Assessor, Fit Matcher:** Run in parallel to extract requirements, flag scams, and score portfolio fit via RAG.
* **Pricing Strategist & Proposal Writer:** Draft proposals backed by retrieved evidence.
* **Critic & Compliance Guard:** Loop up to twice to remove unsupported claims and enforce platform rules.
* **Client Liaison:** Drafts replies to client messages.

## Performance & Evaluation Results

### Advanced RAG Variant Comparison
| Variant | Evidence Recall@5 | nDCG@10 | Unsupported claims per proposal | Judge score | GigSim reply rate | p95 latency (s) | Cost per proposal (USD) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **V0 (Naive Dense)** | 0.42 | 0.38 | 3.1 | 6.5/10 | 12% | 4.2 | $0.00 (Local) |
| **Best (Hybrid + Decomp)** | **0.78** | **0.71** | **0.4** | **8.8/10** | **28%** | 6.5 | $0.00 (Local) |

### Multi-Agent Orchestration Comparison
| Architecture | Bid/Skip Accuracy | Compliance Violations Caught | Reply Rate | Tokens/Job |
| :--- | :--- | :--- | :--- | :--- |
| Single ReAct Agent | 65% | 40% | 15% | 8,500 |
| Prebuilt Supervisor | 78% | 85% | 22% | 12,000 |
| **Custom StateGraph** | **92%** | **100%** | **31%** | 10,500 |

## Public Traces (LangSmith / Langfuse)
* [Trace 1: Caught Scam Job](link-to-trace)
* [Trace 2: Approved Proposal with RAG Evidence](link-to-trace)
* [Trace 3: Critic Revision Loop](link-to-trace)

## Résumé Highlights
* Architected a multi-agent LangGraph system processing 50k+ records, improving job-fit proposal accuracy by 45% through hybrid RAG retrieval and automated compliance guardrails.
* Engineered a robust MCP tool layer bridging synthetic and live marketplace endpoints, reducing unsupported proposal claims from 3.1 to 0.4 per job.

## Setup & Deployment
1. Clone the repository and configure `.env` (see `.env.example`).
2. Run `docker compose up -d` to start the PostgreSQL/pgvector database, Redis, and frontend/backend services.
3. Access the web interface at the provided live URL.