"""`review`: a person's answer to a diagnosis, recorded (roadmap item 10, issue #32,
ADR-0026).

`perfettoagent review <out-dir> accept | reject <reason> | partial <claim-ids>` reads
the verified `diagnosis.json` in `out-dir` and appends one line to
`evals/feedback.jsonl`: the answer, and what it was an answer to, by content. That is
the sha256 of both traces and the range as `diagnose` recorded them (`run.inputs`),
and the sha256 of `diagnosis.json` itself. So a line names exactly one diagnosis of
exactly one pair of traces, wherever the files have moved since, and a rejected
diagnosis can be found again as a candidate eval case.

`partial` names the claims the reviewer accepts; the rest of the kept claims are
recorded as rejected. Only the ids of claims the verifier kept are answerable: a
dropped claim was never shown as a finding.

Nothing here writes anywhere but the feedback file: not the diagnosis, and not the
target repo, which review never reads.
"""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from perfettoagent.diagnosis import DiagnosisInvalid, check_diagnosis
from perfettoagent.evalcases import EVALS_DIR

ANSWERS = ("accept", "reject", "partial")

# Where answers accumulate, beside the eval cases a rejected one may become.
FEEDBACK = EVALS_DIR / "feedback.jsonl"

# Bumped by any change a reader of an older feedback line would misread.
SCHEMA_VERSION = 1

# What `review` reads in an output directory: `diagnose`'s default `--out` name.
DIAGNOSIS_FILE = "diagnosis.json"


class ReviewRefused(ValueError):
    """The answer cannot be recorded as given: no diagnosis, one with no run to name
    its inputs, or claim ids it does not have."""


def review(
    out_dir: str | Path,
    answer: str,
    *,
    reason: str | None = None,
    claim_ids: list[str] | tuple[str, ...] = (),
    feedback: Path = FEEDBACK,
    now: datetime | None = None,
) -> dict:
    """Appends the answer to `feedback` as one JSON line, and returns it.

    `answer` is `accept`, `reject` (with a `reason`) or `partial` (with the
    `claim_ids` accepted). Raises ReviewRefused for anything else, before writing."""
    path = Path(out_dir) / DIAGNOSIS_FILE
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        raise ReviewRefused(f"no {DIAGNOSIS_FILE} in {out_dir}") from None
    try:
        diagnosis = json.loads(raw)
        check_diagnosis(diagnosis)
    except (json.JSONDecodeError, DiagnosisInvalid) as e:
        raise ReviewRefused(f"{path} is not a verified diagnosis: {e}") from e
    if diagnosis["run"] is None:
        raise ReviewRefused(
            f"{path} records no run, so nothing names the traces it diagnosed"
        )
    accepted, rejected = _claims(diagnosis, answer, reason, list(claim_ids))

    run = diagnosis["run"]
    line = {
        "schema": SCHEMA_VERSION,
        "reviewed_at": (now or datetime.now(UTC)).isoformat(timespec="seconds"),
        "answer": answer,
        "reason": reason,
        "claims_accepted": accepted,
        "claims_rejected": rejected,
        "inputs": {
            **run["inputs"],
            "diagnosis_sha256": hashlib.sha256(raw).hexdigest(),
        },
        "diagnosis": {
            "verdict": diagnosis["verdict"],
            "culprit": diagnosis["culprit"]["commit"] if diagnosis["culprit"] else None,
            "metric": diagnosis["metric"]["name"] if diagnosis["metric"] else None,
            "provider": run["provider"],
            "model": run["model"],
            "effort": run["effort"],
        },
    }
    feedback.parent.mkdir(parents=True, exist_ok=True)
    with feedback.open("a") as f:
        f.write(json.dumps(line, sort_keys=True) + "\n")
    return line


def _claims(
    diagnosis: dict, answer: str, reason: str | None, claim_ids: list[str]
) -> tuple[list[str], list[str]]:
    """(accepted, rejected) claim ids for the answer, or ReviewRefused."""
    kept = [c["id"] for c in diagnosis["claims"]]
    if answer == "accept":
        return kept, []
    if answer == "reject":
        if not reason or not reason.strip():
            raise ReviewRefused("reject needs a reason")
        return [], kept
    if answer != "partial":
        raise ReviewRefused(f"the answer is one of {ANSWERS}, not {answer!r}")
    unknown = [c for c in claim_ids if c not in kept]
    if unknown:
        raise ReviewRefused(
            f"no kept claim {', '.join(unknown)}; this diagnosis's claims are "
            + (", ".join(kept) or "none")
        )
    accepted = [c for c in kept if c in claim_ids]
    if not accepted or len(accepted) == len(kept):
        raise ReviewRefused(
            "partial accepts some claims and not others; use accept or reject"
        )
    return accepted, [c for c in kept if c not in claim_ids]
