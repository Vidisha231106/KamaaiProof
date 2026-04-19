# Documentation Hub

This folder contains role-specific execution specifications for the KamaaiProof build.

## Files

1. `01-Frontend-Spec.md`
2. `02-LangChain-Parsing-Spec.md`
3. `03-Scoring-Firebase-PDF-Spec.md`
4. `04-DevOps-QA-Spec.md`

## How to Use These Documents

- Use each spec as a role handbook.
- Follow the execution order inside each file.
- When assigning AI agents, reference the exact spec file and section.
- Keep implementation aligned with shared contracts in the root README.

## Guidance for AI Agents

Before coding:

1. Read root README for architecture and constraints.
2. Read relevant role spec in this folder.
3. Read module README in target code folder.
4. Confirm assumptions around API shape and privacy rules.

## Maintenance Rule

When implementation changes invalidate a spec, update this folder immediately so future contributors do not follow stale instructions.
