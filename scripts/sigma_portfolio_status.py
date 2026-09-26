#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, pathlib, sys, yaml

ROOT=pathlib.Path(__file__).resolve().parents[1]
POLICY=ROOT/"headquarters/orchestration/policy.yaml"
PROJECTS=ROOT/"headquarters/orchestration/projects"
ALLOWED={"PLANNED","RUNNING","CHANGED","TESTED","VERIFIED_IN_PRODUCTION","BLOCKED"}

def parse_time(value):
    if not value: return None
    return dt.datetime.fromisoformat(str(value).replace("Z","+00:00"))

def load(path):
    with path.open(encoding="utf-8") as f: return yaml.safe_load(f)

def validate_record(d):
    errors=[]
    state=((d.get("cycle") or {}).get("state"))
    if state not in ALLOWED: errors.append(f"invalid state {state!r}")
    evidence=d.get("evidence") or []
    if state in {"CHANGED","TESTED","VERIFIED_IN_PRODUCTION"} and not evidence:
        errors.append("NO EVIDENCE = NO PROGRESS: promoted state has no durable evidence")
    tests=d.get("tests") or {}
    if state in {"TESTED","VERIFIED_IN_PRODUCTION"} and not (tests.get("evidence") or []):
        errors.append("TESTED or higher requires exact-candidate test evidence")
    prod=d.get("production") or {}
    if state=="VERIFIED_IN_PRODUCTION" and not (prod.get("commit") and prod.get("verified_at")):
        errors.append("VERIFIED_IN_PRODUCTION requires production commit and verified_at")
    return errors

def status(d, now, stale_hours):
    last=parse_time((d.get("cycle") or {}).get("last_evidenced_at"))
    stale=(last is None) or ((now-last).total_seconds()>stale_hours*3600)
    return "STALE" if stale else (d.get("cycle") or {}).get("state","PLANNED")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--now", help="ISO timestamp for deterministic tests")
    ap.add_argument("--strict", action="store_true")
    args=ap.parse_args()
    policy=load(POLICY)
    stale_hours=int(policy["freshness"]["stale_after_hours"])
    now=parse_time(args.now) if args.now else dt.datetime.now(dt.timezone.utc)
    failures=0
    print("| Project | State | Freshness | Commit | Tests | Mobile | AI Assist | PDF Chat | Next cycle |")
    print("|---|---|---|---|---|---|---|---|---|")
    for path in sorted(PROJECTS.glob("*.yaml")):
        d=load(path); errors=validate_record(d); failures+=len(errors)
        derived=status(d,now,stale_hours)
        t=d.get("tests") or {}; passed=t.get("passed"); failed=t.get("failed")
        tests="NOT VERIFIED" if passed is None or failed is None else f"{passed} passed / {failed} failed"
        caps=d.get("capabilities") or {}
        row=[d.get("project","?"),(d.get("cycle") or {}).get("state","?"),derived,(d.get("source") or {}).get("commit") or "UNKNOWN",tests,(d.get("journeys") or {}).get("mobile","NOT_VERIFIED"),(caps.get("ai_assist") or {}).get("status","NOT_VERIFIED"),(caps.get("pdf_chat") or {}).get("status","NOT_VERIFIED"),(d.get("next_cycle") or {}).get("action","")]
        print("| "+" | ".join(str(x).replace("|","/") for x in row)+" |")
        for e in errors: print(f"ERROR {path.name}: {e}",file=sys.stderr)
    if args.strict and failures: return 1
    return 0
if __name__=="__main__": raise SystemExit(main())
