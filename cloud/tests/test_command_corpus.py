"""Corpus generator tests — expansion scale, splits, recording sheets, round-trip."""
import csv
import json
from pathlib import Path

import yaml

from data.build_command_corpus import expand_corpus, reference_intent, write_outputs

GRAMMAR = yaml.safe_load(open(Path(__file__).resolve().parent.parent / "configs" / "commands.yaml"))


def test_expansion_scale_and_uniqueness():
    rows = expand_corpus(GRAMMAR, max_utts=2000, seed=42)
    assert 500 < len(rows) <= 2000
    ids = [r["id"] for r in rows]
    assert len(set(ids)) == len(ids)                     # unique utterance ids
    assert len(set(r["text"] for r in rows)) > len(rows) * 0.9   # few text dupes


def test_splits_present_and_majority_train():
    rows = expand_corpus(GRAMMAR, max_utts=2000, seed=42)
    splits = [r["split"] for r in rows]
    for s in ("train", "dev", "test"):
        assert s in splits
    assert splits.count("train") > 0.85 * len(rows)


def test_reference_intent_parseable_by_router():
    """Ground truth must be reachable through the router itself (self-consistency)."""
    from serving.intent_router import IntentRouter
    router = IntentRouter(Path(__file__).resolve().parent.parent / "configs" / "commands.yaml")
    rows = expand_corpus(GRAMMAR, max_utts=2000, seed=42)
    exact = 0
    for r in rows:
        i = router.parse(r["text"])
        if i["type"] == "command" and i["action"] == r["action"] and \
                i["subsystem"] == r["subsystem"]:
            exact += 1
    assert exact / len(rows) > 0.99            # grammar self-consistency


def test_write_outputs_schema(tmp_path):
    rows = expand_corpus(GRAMMAR, max_utts=100, seed=1)
    write_outputs(rows, tmp_path, ["alice", "bob"])
    meta = list(csv.DictReader(open(tmp_path / "metadata.csv")))
    assert len(meta) == len(rows)
    manifest = [json.loads(l) for l in open(tmp_path / "manifest.jsonl")]
    assert manifest[0]["corpus"] == "agni_commands"
    assert "reference_intent" in manifest[0]
    sheets = list(tmp_path.glob("recorder_sheet_*.md"))
    assert len(sheets) == 2
    assert all("AGNI_" in s.read_text() for s in sheets)
