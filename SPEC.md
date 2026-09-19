# EvidenceGraph specification

## Proof obligation

Establish whether a sealed natural-language claim is supported, contradicted, or left insufficient by two or three exact, independently fetched documents bound to immutable GitHub commits.

## Falsifier

A committed document that materially contradicts the claim under the sealed evaluation criteria, a digest mismatch, or evidence that does not contain enough information to establish the claim.

## Evidence architecture

Callers provide only GitHub owner, repository, full commit SHA, path and expected SHA-256. The contract constructs `raw.githubusercontent.com` URLs. Each validator fetches the exact bytes, recomputes SHA-256, and judges the semantic relationship between each document and the sealed claim.

## Judgment boundary

Validators classify each evidence item as `SUPPORTS`, `CONTRADICTS`, or `INSUFFICIENT`. They cannot change sources, lifecycle, authorization, finalization, or the final deterministic precedence.

## Deterministic outcome

- unavailable source: `ASSESSMENT_RETRYABLE`, no mutation;
- digest mismatch: `INTEGRITY_FAILURE`;
- any combination of support and contradiction: `MIXED_EVIDENCE`;
- at least two supports and no contradiction: `SUPPORTED`;
- any contradiction without the support threshold: `CONTRADICTED`;
- otherwise: `INSUFFICIENT_EVIDENCE`.

## Lifecycle

`DRAFT -> SEALED -> ASSESSED -> CHALLENGED -> RESOLVED`.

Draft evidence is creator-controlled. Sealing freezes the evidence set. A non-creator can open one challenge against an assessed case and attach one immutable counter-evidence item. Reassessment resolves the challenge. Historical evidence is never overwritten.
