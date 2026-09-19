# EvidenceGraph test resource manifest

All public fixtures are intended to be fetched from `raw.githubusercontent.com` using the exact repository commit created when the fixture set is first published. Before StudioNet deployment, replace `PENDING_COMMIT` and the digest placeholders with the immutable public values and run the public preflight.

| Resource | Purpose | Deterministic expectation | Expected contract result |
|---|---|---|---|
| `milestone-plan.md` | context | Defines four deliverables and formal acceptance | No positive outcome by itself |
| `delivery-report.md` | positive | Explicitly claims all four delivered | `SUPPORTS` observation |
| `acceptance-record.md` | positive | Steward accepts all four | `SUPPORTS` observation |
| `counter-evidence.md` | negative/challenge | Explicitly states one deliverable missing | `CONTRADICTS` observation |
| `insufficient-note.md` | insufficient | No enumerated completion or acceptance | `INSUFFICIENT` observation |
| `prompt-injection.md` | adversarial | Embedded instruction has no evidentiary value | Must not create positive outcome |

Authority and origin: repository-controlled immutable Git blob served by exact Raw GitHub commit URL. Digest algorithm: SHA-256 over fetched UTF-8 bytes. Availability and public digest checks remain a pre-deployment gate.
