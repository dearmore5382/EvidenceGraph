"""Checkpointed two-wallet StudioNet lifecycle. Signed writes are never retried."""
import base64
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from genlayer_py import create_account, create_client
from genlayer_py.abi import calldata
from genlayer_py.abi.transactions import serialize
from genlayer_py.chains import studionet

ROOT = Path(__file__).resolve().parents[1]
ADDRESS = "0xff14db8477421e0FBC3c9865b4a0350Bc0c7C063"
RPC = "https://studio.genlayer.com/api"
SOURCE_HASH = "398f8f6ff2b4fc2679eb84964e1f20f65650a58a2f5e38e7d3b772ba4526ae1f"
OWNER, REPO = "dearmore5382", "NoticeClause-Gate"
COMMIT = "21d3f20353583b1ff50129de2f6fee037a66b550"
SUPPORT_A = ("fixtures/compliant.txt", "af1dc913caa85cd32622a3c742692fdc94552eb66b5e9b1160f8d8e1ba789266")
SUPPORT_B = ("verification/LIVE_RESULTS.md", "daa95baee3b3c9b539f991291178be7aef094ec26d8219c820783c5e1934e754")
COUNTER = ("fixtures/wrong-reference.txt", "1c49bc9969e287be60bcb2d717bc25a29ea3463c59eb38cfdd9ae5f7e34ac933")
TITLE = "Notice clause content verification"
CLAIM = "The notice states termination because monthly uptime fell below 95%, effective 2026-10-01, under Agreement SVC-2026-017."
CRITERIA = "SUPPORTS requires all three exact facts: uptime below 95% as the reason, effective date 2026-10-01, and Agreement SVC-2026-017. A different agreement reference CONTRADICTS the claim."
PRIVATE = ROOT / ".private" / ("live-" + ADDRESS.lower() + ".json")
PUBLIC = ROOT / "verification" / ("live-" + ADDRESS.lower() + ".json")
TEST_ENV = ROOT.parent / "DAOProposalContextVerifier" / ".env.lifecycle"


def rpc(method, params):
    response = requests.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, timeout=60)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError("RPC_ERROR:" + str(data["error"].get("message")))
    return data["result"]


def view(method, args=None, sender="0x0000000000000000000000000000000000000001"):
    data = serialize([calldata.encode({"method": method, "args": args or []}), b"\x00"])
    raw = rpc("gen_call", [{"type": "read", "to": ADDRESS, "from": sender, "value": "0x0", "data": data,
                            "transaction_hash_variant": "latest-final"}])
    return str(calldata.decode(bytes.fromhex(raw.removeprefix("0x"))))


def parity_and_sources():
    deployed = base64.b64decode(rpc("gen_getContractCode", [ADDRESS]))
    local = (ROOT / "contracts" / "EvidenceGraph.py").read_bytes()
    if deployed != local or hashlib.sha256(deployed).hexdigest() != SOURCE_HASH:
        raise RuntimeError("SOURCE_MISMATCH")
    base = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{COMMIT}/"
    for path, expected in (SUPPORT_A, SUPPORT_B, COUNTER):
        body = requests.get(base + path, timeout=45).content
        if hashlib.sha256(body).hexdigest() != expected:
            raise RuntimeError("FIXTURE_DIGEST_MISMATCH:" + path)


def keys():
    values = {}
    for raw in TEST_ENV.read_text(encoding="utf-8").splitlines():
        if raw.strip() and not raw.lstrip().startswith("#") and "=" in raw:
            key, value = raw.split("=", 1)
            values[key.strip()] = value.strip()
    result = [os.environ.get("WALLET_A_PRIVATE_KEY") or values.get("WALLET_A_PRIVATE_KEY"),
              os.environ.get("WALLET_B_PRIVATE_KEY") or values.get("WALLET_B_PRIVATE_KEY")]
    if not all(result):
        raise RuntimeError("LOCAL_TEST_KEYS_NOT_FOUND")
    return result


def tx_return(tx):
    receipts = (tx.get("consensus_data") or {}).get("leader_receipt") or []
    receipts = [receipts] if isinstance(receipts, dict) else receipts
    leaders = [item for item in receipts if item.get("mode") == "leader"]
    if not leaders or leaders[-1].get("execution_result") != "SUCCESS":
        raise RuntimeError("LEADER_EXECUTION_FAILED")
    value = leaders[-1].get("result")
    raw = base64.b64decode(value["raw"] if isinstance(value, dict) else value)
    if not raw or raw[0] != 0:
        raise RuntimeError("CONTRACT_EXECUTION_ERROR")
    return str(calldata.decode(raw[1:]))


def save(record):
    PRIVATE.parent.mkdir(exist_ok=True)
    PRIVATE.write_text(json.dumps(record, indent=2), encoding="utf-8")
    public = json.loads(json.dumps(record))
    public.pop("balances", None)
    for step in public["steps"]:
        step.pop("receipt", None)
    PUBLIC.write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")


def main():
    private_keys = keys()
    accounts = [create_account(account_private_key="0x" + key.removeprefix("0x")) for key in private_keys]
    del private_keys
    creator, challenger = accounts
    clients = {a.address.lower(): create_client(chain=studionet, account=a) for a in accounts}
    parity_and_sources()
    balances = {a.address: int(rpc("eth_getBalance", [a.address, "latest"]), 16) for a in accounts}
    plan = [
        {"id":"H1-create","actor":creator.address,"method":"create_case","args":[TITLE,CLAIM,CRITERIA],"allowed":["0"]},
        {"id":"H2-support-a","actor":creator.address,"method":"add_evidence","args":[0,"SUPPORT",OWNER,REPO,COMMIT,SUPPORT_A[0],SUPPORT_A[1]],"allowed":["EVIDENCE_ADDED"]},
        {"id":"H3-support-b","actor":creator.address,"method":"add_evidence","args":[0,"SUPPORT",OWNER,REPO,COMMIT,SUPPORT_B[0],SUPPORT_B[1]],"allowed":["EVIDENCE_ADDED"]},
        {"id":"H4-seal","actor":creator.address,"method":"seal_case","args":[0],"allowed":["CASE_SEALED"]},
        {"id":"H5-assess","actor":challenger.address,"method":"assess_case","args":[0],"allowed":["INSUFFICIENT_EVIDENCE"]},
        {"id":"H6-challenge","actor":challenger.address,"method":"open_challenge","args":[0,"A source using Agreement OTHER-01 contradicts the sealed exact-reference claim."],"allowed":["CHALLENGE_OPENED"]},
        {"id":"H7-counter","actor":challenger.address,"method":"add_evidence","args":[0,"COUNTER",OWNER,REPO,COMMIT,COUNTER[0],COUNTER[1]],"allowed":["EVIDENCE_ADDED"]},
        {"id":"H8-resolve","actor":creator.address,"method":"assess_case","args":[0],"allowed":["MIXED_EVIDENCE"]},
        {"id":"P1-create-happy","actor":creator.address,"method":"create_case","args":["Agenda scope happy path","Repairing broken onboarding documentation links is permitted by the community website maintenance agenda.","SUPPORTS requires explicit permission for documentation-link repair."],"allowed":["1"]},
        {"id":"P2-happy-agenda","actor":creator.address,"method":"add_evidence","args":[1,"SUPPORT","dearmore5382","AgendaScopeGate","03b9e05b89fa4bb17ad02248a8172495cf75b25c","fixtures/agenda.txt","7b5c1b4785eb8fc02f30eccde4060cb7909989c885a039c5dbed73e017239210"],"allowed":["EVIDENCE_ADDED"]},
        {"id":"P3-happy-motion","actor":creator.address,"method":"add_evidence","args":[1,"SUPPORT","dearmore5382","AgendaScopeGate","03b9e05b89fa4bb17ad02248a8172495cf75b25c","fixtures/in-scope.txt","59caf88920f73b84de861139fce82d507aed998990705eb484b419e1f567609a"],"allowed":["EVIDENCE_ADDED"]},
        {"id":"P4-happy-seal","actor":creator.address,"method":"seal_case","args":[1],"allowed":["CASE_SEALED"]},
        {"id":"P5-happy-assess","actor":challenger.address,"method":"assess_case","args":[1],"allowed":["INSUFFICIENT_EVIDENCE"]},
        {"id":"P6-create-independent-happy","actor":creator.address,"method":"create_case","args":["AgendaScopeGate live verification","The AgendaScopeGate StudioNet lifecycle completed with source parity and an in-scope documentation-link repair result.","SUPPORTS requires the report to state completed live verification and the documentation-link repair outcome."],"allowed":["2"]},
        {"id":"P7-happy-report-a","actor":creator.address,"method":"add_evidence","args":[2,"SUPPORT","dearmore5382","AgendaScopeGate","03b9e05b89fa4bb17ad02248a8172495cf75b25c","verification/studionet-e2e-current.md","6cb1537a751c26ed1759bcc5bbf66fce5fc506316ea3867236a4de7c22b13fd5"],"allowed":["EVIDENCE_ADDED"]},
        {"id":"P8-happy-report-b","actor":creator.address,"method":"add_evidence","args":[2,"SUPPORT","dearmore5382","AgendaScopeGate","03b9e05b89fa4bb17ad02248a8172495cf75b25c","verification/release-evidence.md","507722c996a79655ca3ac5a22d04c103e1e5fe3c144a2ba2ccd5f7f1b8a9ada3"],"allowed":["EVIDENCE_ADDED"]},
        {"id":"P9-independent-happy-seal","actor":creator.address,"method":"seal_case","args":[2],"allowed":["CASE_SEALED"]},
        {"id":"P10-independent-happy-assess","actor":challenger.address,"method":"assess_case","args":[2],"allowed":["INSUFFICIENT_EVIDENCE"]},
        {"id":"F1-create-contradiction","actor":creator.address,"method":"create_case","args":["Agenda exclusions","Minting governance tokens and transferring treasury funds are permitted website-maintenance actions.","CONTRADICTS when either claimed financial action is explicitly excluded or unauthorized."],"allowed":["3"]},
        {"id":"F2-exclusion","actor":creator.address,"method":"add_evidence","args":[3,"SUPPORT","dearmore5382","AgendaScopeGate","03b9e05b89fa4bb17ad02248a8172495cf75b25c","fixtures/explicit-exclusion.txt","4fde473896728b4e83e2e2d46d19bf86eaef760769e3dfbef7b7191a97804650"],"allowed":["EVIDENCE_ADDED"]},
        {"id":"F3-injection-motion","actor":creator.address,"method":"add_evidence","args":[3,"CONTEXT","dearmore5382","AgendaScopeGate","03b9e05b89fa4bb17ad02248a8172495cf75b25c","fixtures/prompt-injection.txt","727e1be7632c86d531774b614aca72f9c1dbb019754524d9a8ab7ad68d1153a1"],"allowed":["EVIDENCE_ADDED"]},
        {"id":"F4-contradiction-seal","actor":creator.address,"method":"seal_case","args":[3],"allowed":["CASE_SEALED"]},
        {"id":"F5-contradiction-assess","actor":challenger.address,"method":"assess_case","args":[3],"allowed":["INSUFFICIENT_EVIDENCE"]},
        {"id":"I1-create-integrity","actor":creator.address,"method":"create_case","args":["Integrity failure","The notice has a clear reason and effective date.","Assess only after both source digests match."],"allowed":["4"]},
        {"id":"I2-false-digest","actor":creator.address,"method":"add_evidence","args":[4,"SUPPORT","dearmore5382","NoticeClause-Gate",COMMIT,"fixtures/missing-reason.txt","0"*64],"allowed":["EVIDENCE_ADDED"]},
        {"id":"I3-second-source","actor":creator.address,"method":"add_evidence","args":[4,"CONTEXT","dearmore5382","NoticeClause-Gate",COMMIT,"fixtures/unclear-date.txt","57b7801fadde19c63627a9aa87bc5922b74f96b4b52b217598413c34c642f484"],"allowed":["EVIDENCE_ADDED"]},
        {"id":"I4-integrity-seal","actor":creator.address,"method":"seal_case","args":[4],"allowed":["CASE_SEALED"]},
        {"id":"I5-integrity-assess","actor":challenger.address,"method":"assess_case","args":[4],"allowed":["INTEGRITY_FAILURE"]},
        {"id":"U1-create-unavailable","actor":creator.address,"method":"create_case","args":["Unavailable retry","The notice is compliant.","Unavailable sources must not mutate the sealed case."],"allowed":["5"]},
        {"id":"U2-live-source","actor":creator.address,"method":"add_evidence","args":[5,"SUPPORT","dearmore5382","NoticeClause-Gate",COMMIT,"fixtures/prompt-injection.txt","b5b4705689c4601706b9632d01052209e1967a7118267d5d7912ccd344dcc95c"],"allowed":["EVIDENCE_ADDED"]},
        {"id":"U3-dead-source","actor":creator.address,"method":"add_evidence","args":[5,"CONTEXT","dearmore5382","NoticeClause-Gate",COMMIT,"fixtures/does-not-exist.md","1"*64],"allowed":["EVIDENCE_ADDED"]},
        {"id":"U4-unavailable-seal","actor":creator.address,"method":"seal_case","args":[5],"allowed":["CASE_SEALED"]},
        {"id":"U5-unavailable-assess","actor":challenger.address,"method":"assess_case","args":[5],"allowed":["ASSESSMENT_RETRYABLE"]},
    ]
    if PRIVATE.exists():
        record = json.loads(PRIVATE.read_text(encoding="utf-8"))
    else:
        if view("get_count", sender=creator.address) != "0":
            raise RuntimeError("EXPECTED_EMPTY_DEPLOYMENT")
        record = {"contract":ADDRESS,"source_sha256":SOURCE_HASH,"fixture_repository":f"{OWNER}/{REPO}",
                  "fixture_commit":COMMIT,"started_at":datetime.now(timezone.utc).isoformat(),
                  "wallets":[a.address for a in accounts],"balances":balances,"steps":[],"complete":False}
        save(record)
    print(json.dumps({"ready":True,"wallets":record["wallets"],"balances":balances,"completed":len(record["steps"]),"total":len(plan)}), flush=True)
    for index, wanted in enumerate(plan):
        parity_and_sources()
        if index < len(record["steps"]):
            item = record["steps"][index]
            if item["id"] != wanted["id"]:
                raise RuntimeError("PLAN_MISMATCH")
            item["allowed"] = wanted["allowed"]
            save(record)
            if item.get("status") == "VERIFIED":
                continue
            if item.get("status") != "SUBMITTED":
                raise RuntimeError("UNKNOWN_CHECKPOINT")
        else:
            item = dict(wanted)
            item["status"] = "INTENT_SAVED"
            record["steps"].append(item)
            save(record)
            item["hash"] = str(clients[item["actor"].lower()].write_contract(address=ADDRESS, function_name=item["method"], args=item["args"], value=0, leader_only=False))
            item["status"] = "SUBMITTED"
            save(record)
            print(json.dumps({"step":item["id"],"hash":item["hash"]}), flush=True)
        deadline = time.monotonic() + 1200
        while time.monotonic() < deadline:
            tx = rpc("eth_getTransactionByHash", [item["hash"]])
            if tx and tx.get("status") == "FINALIZED":
                if tx.get("result_name") != "MAJORITY_AGREE":
                    raise RuntimeError("CONSENSUS_FAILED")
                actual = tx_return(tx)
                if actual not in item["allowed"]:
                    raise RuntimeError("UNEXPECTED:" + actual)
                readback = {"count":int(view("get_count", sender=creator.address))}
                if readback["count"]:
                    readback["case0"] = view("get_case", [0], creator.address)
                item.update({"actual":actual,"receipt":tx,"readback":readback,"status":"VERIFIED",
                             "explorer":"https://explorer-studio.genlayer.com/tx/" + item["hash"]})
                save(record)
                print(json.dumps({"step":item["id"],"actual":actual}), flush=True)
                break
            time.sleep(8)
        else:
            raise RuntimeError("POLL_TIMEOUT_KEEP_HASH")
    record["complete"] = True
    record["completed_at"] = datetime.now(timezone.utc).isoformat()
    save(record)
    print(json.dumps({"complete":True,"steps":len(plan),"final":view("get_case",[0],creator.address)}), flush=True)


if __name__ == "__main__":
    main()
