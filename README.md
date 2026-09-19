# EvidenceGraph

EvidenceGraph is a multi-source GenLayer claim-verification DApp. A case creator seals a claim, criteria, and two or three commit-pinned GitHub documents. Validators independently fetch exact bytes, recompute SHA-256, and classify how each source relates to the claim. Deterministic contract code derives the outcome and controls the challenge lifecycle.

Possible outcomes are `SUPPORTED`, `CONTRADICTED`, `MIXED_EVIDENCE`, `INSUFFICIENT_EVIDENCE`, and `INTEGRITY_FAILURE`. A temporarily unavailable source returns `ASSESSMENT_RETRYABLE` without changing case state.

## Architecture

This project uses a case/evidence/challenge graph rather than a one-shot document audit. Evidence is append-only, sealing freezes the initial set, a different wallet may open one challenge and attach counter-evidence, and reassessment resolves without overwriting history.

The frontend uses a public website architecture with a narrative landing page, public case explorer, and dedicated case builder. It does not reuse the artifact-comparison layout from earlier projects.

## Local verification

```bash
pytest -q
cd frontend
npm run build
```

The Direct Mode suite exercises authorization, lifecycle locking, global source replay prevention, raw-source fetching, SHA-256 mismatch handling, retry-without-mutation, validator re-execution, and challenge resolution.

## Live deployment

- Public DApp: https://evidencegraph.dearmorescheuer5382.workers.dev
- StudioNet contract: `0xff14db8477421e0FBC3c9865b4a0350Bc0c7C063`
- Exact deployed source SHA-256: `398f8f6ff2b4fc2679eb84964e1f20f65650a58a2f5e38e7d3b772ba4526ae1f`
- Two-wallet lifecycle: complete
- Final case `0`: `RESOLVED / MIXED_EVIDENCE`

Explorer-linked evidence and authoritative readbacks are in `verification/LIVE_RESULTS.md` and the adjacent machine-readable JSON journal.
