# Backend Source Overview

This folder is the backend implementation root.

## Folder Roles

- `api/`: HTTP routes and request/response handling
- `chains/`: LangChain extraction logic and orchestration
- `services/`: scoring, persistence, and shared business logic

## Backend Pipeline Summary

1. API layer accepts uploaded files and metadata.
2. Chains layer extracts structured data per document category.
3. Services layer computes score and flags, then persists approved summaries.
4. API layer returns normalized output to frontend.

## Implementation Priorities

1. Health and parse routes
2. Extraction chains and schema enforcement
3. Scoring algorithm and flags
4. Firebase persistence and sanitization
5. Reliability hardening and test coverage

## Editing Guidelines for AI Agents

1. Keep route handlers thin.
2. Keep extraction schemas explicit and version-aware.
3. Keep scoring deterministic and testable.
4. Apply privacy guardrails before persistence.
