from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "contracts" / "EvidenceGraph.py").read_text(encoding="utf-8")

def derive(observation):
    if observation.get("status") == "UNAVAILABLE": return "ASSESSMENT_RETRYABLE"
    if observation.get("status") == "INTEGRITY_FAILURE": return "INTEGRITY_FAILURE"
    findings = observation.get("findings", [])
    supports = findings.count("SUPPORTS")
    contradicts = findings.count("CONTRADICTS")
    if supports >= 1 and contradicts >= 1: return "MIXED_EVIDENCE"
    if supports >= 2: return "SUPPORTED"
    if contradicts >= 1: return "CONTRADICTED"
    return "INSUFFICIENT_EVIDENCE"

def test_source_shape_and_authority():
    ast.parse(SOURCE)
    assert SOURCE.startswith('# v0.2.16\n# { "Depends":')
    assert "https://raw.githubusercontent.com/" in SOURCE
    assert "run_nondet_unsafe" in SOURCE
    tree = ast.parse(SOURCE)
    add = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "add_evidence")
    assert all("url" not in arg.arg.lower() for arg in add.args.args)

def test_verdict_precedence():
    assert derive({"status":"UNAVAILABLE"}) == "ASSESSMENT_RETRYABLE"
    assert derive({"status":"INTEGRITY_FAILURE"}) == "INTEGRITY_FAILURE"
    assert derive({"status":"VERIFIED","findings":["SUPPORTS","SUPPORTS","INSUFFICIENT"]}) == "SUPPORTED"
    assert derive({"status":"VERIFIED","findings":["SUPPORTS","CONTRADICTS"]}) == "MIXED_EVIDENCE"
    assert derive({"status":"VERIFIED","findings":["SUPPORTS","SUPPORTS","CONTRADICTS"]}) == "MIXED_EVIDENCE"
    assert derive({"status":"VERIFIED","findings":["SUPPORTS","INSUFFICIENT"]}) == "INSUFFICIENT_EVIDENCE"

def test_lifecycle_and_replay_guards_present():
    for token in ("DRAFT", "SEALED", "ASSESSED", "CHALLENGED", "RESOLVED", "SOURCE_ALREADY_USED", "CREATOR_ONLY", "CHALLENGER_ONLY"):
        assert token in SOURCE
