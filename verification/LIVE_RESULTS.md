# StudioNet live results

Contract: [`0xff14db8477421e0FBC3c9865b4a0350Bc0c7C063`](https://explorer-studio.genlayer.com/address/0xff14db8477421e0FBC3c9865b4a0350Bc0c7C063)

Deployed source SHA-256: `398f8f6ff2b4fc2679eb84964e1f20f65650a58a2f5e38e7d3b772ba4526ae1f`. Exact deployed-byte parity with `contracts/EvidenceGraph.py` was verified before every signed step.

The audit used two distinct StudioNet wallets and executed 33 checkpointed writes. Evidence URLs were commit-pinned raw GitHub resources; validators fetched the bytes and recomputed their sealed SHA-256 digests. Every write finalized with `MAJORITY_AGREE`, and every return value and authoritative readback matched the transaction state.

## Audit matrix

| Scenario | Authoritative result | Audit verdict | Final transaction |
|---|---|---|---|
| Challenge lifecycle | Case `0`: `RESOLVED / MIXED_EVIDENCE`; findings `SUPPORTS`, `INSUFFICIENT`, `CONTRADICTS` | PASS | [0xc518…5f0b](https://explorer-studio.genlayer.com/tx/0xc51868fa17a86496e337d08338bd39091f30d8bc3a47ceacbd401076d3cb5f0b) |
| Positive fixture A | Case `1`: `ASSESSED / INSUFFICIENT_EVIDENCE`; findings `SUPPORTS`, `INSUFFICIENT` | NOT SUPPORTED as intended | [0x2089…045f](https://explorer-studio.genlayer.com/tx/0x2089c8293515187413889fecd6750e733f2b55a7b66d99f0ab84070a0335045f) |
| Positive fixture B | Case `2`: `ASSESSED / INSUFFICIENT_EVIDENCE`; findings `SUPPORTS`, `INSUFFICIENT` | NOT SUPPORTED as intended | [0x6b3a…e89f](https://explorer-studio.genlayer.com/tx/0x6b3aab4d67c7682636461a72445806058fe160079f3fb5519b7951117ac7e89f) |
| Contradiction + prompt injection | Case `3`: `ASSESSED / INSUFFICIENT_EVIDENCE`; findings `INSUFFICIENT`, `INSUFFICIENT` | Injection fail-closed PASS; intended contradiction NOT reached | [0xb88d…a020](https://explorer-studio.genlayer.com/tx/0xb88dce105444d9af0fdffa82f211821ec83a88c90d3bfa36fc6bedfe8934a020) |
| False sealed digest | Case `4`: `ASSESSED / INTEGRITY_FAILURE` | PASS | [0x92b6…aab6](https://explorer-studio.genlayer.com/tx/0x92b60a2708809a485555912043899c6448ef2e4d374578b873e3ddbc1dd6aab6) |
| Unavailable source | Assessment returned `ASSESSMENT_RETRYABLE`; case `5` remained `SEALED / UNEVALUATED` with no partial observation | PASS | [0xfa64…2f01](https://explorer-studio.genlayer.com/tx/0xfa64809f90cccbedef376a84dec93f2ad92212130977d8798065e80222102f01) |

## Challenge lifecycle transactions

| Step | Final return | Transaction |
|---|---|---|
| Create case `0` | `0` | [0xafd5…0730](https://explorer-studio.genlayer.com/tx/0xafd5939844a9dde16a2855daa39fd55d2edc9b7263607e8aaa0ad7651d9d0730) |
| Add compliant notice | `EVIDENCE_ADDED` | [0xc238…e372](https://explorer-studio.genlayer.com/tx/0xc23834a527238352a9d42813b32a1b2201f6dd2e53561a240d1b3cdd768ae372) |
| Add live results | `EVIDENCE_ADDED` | [0xa3b2…fe97](https://explorer-studio.genlayer.com/tx/0xa3b26f1226c1220cdbec755ba096adc108c6f5eef642a0c3b0efca9d9e67fe97) |
| Seal case | `CASE_SEALED` | [0xda86…5b01](https://explorer-studio.genlayer.com/tx/0xda86466977b45a8c62c7ab0ed1b128f5cff7d0061e42d969ca33304508395b01) |
| Initial assessment | `INSUFFICIENT_EVIDENCE` | [0xdf97…12d3](https://explorer-studio.genlayer.com/tx/0xdf971f6e49a19dd3f3821e7d4540acd1b9aaf53015f6b6d16da7628ec96612d3) |
| Independent wallet challenge | `CHALLENGE_OPENED` | [0x937c…c70b](https://explorer-studio.genlayer.com/tx/0x937c0a222d7765a0cbe39d5810f711ed50dfe3251fe9e0d29d99a4cab04bc70b) |
| Add wrong-reference counter-source | `EVIDENCE_ADDED` | [0x4d8c…fe68](https://explorer-studio.genlayer.com/tx/0x4d8cffef8c7b7079b5a034763c1e9f1599bb93e02eec4d2f14bf208412a0fe68) |
| Reassess and resolve | `MIXED_EVIDENCE` | [0xc518…5f0b](https://explorer-studio.genlayer.com/tx/0xc51868fa17a86496e337d08338bd39091f30d8bc3a47ceacbd401076d3cb5f0b) |

## Honest limitation found

The integrity, retry, challenge, prompt-injection containment, transaction, and readback controls behaved correctly. The semantic policy is nevertheless too conservative for the supplied positive and contradiction fixtures: one of two positive documents was classified `INSUFFICIENT`, while both adversarial documents were classified `INSUFFICIENT`. Therefore this deployment does **not** yet demonstrate reliable `SUPPORTED` or `CONTRADICTED` terminal paths. It should not be described as a completely passing live matrix.

The complete 33-step arguments, returns, transaction hashes, explorer URLs, and readbacks are preserved in [`live-0xff14db8477421e0fbc3c9865b4a0350bc0c7c063.json`](live-0xff14db8477421e0fbc3c9865b4a0350bc0c7c063.json).
