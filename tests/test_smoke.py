"""Smoke tests: intent parsing, pipeline wiring, HTTP /run."""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from packages.agents.intent_extractor import extract_event_intent
from packages.agents.run_intelligence import PipelineConfig, run_pipeline


def test_extract_labeled_intent():
    text = (
        "Event type: dinner\n"
        "People we want: founders and CTOs\n"
        "Goal: real intros\n"
    )
    d = extract_event_intent(text)
    assert "dinner" in (d.get("event_type") or "").lower()
    assert "founders" in (d.get("desired_attendees") or "").lower()


def test_run_pipeline_empty_brief():
    code, meta = run_pipeline("", quiet=True)
    assert code == 2
    assert meta.get("error") == "empty_brief"


def test_run_pipeline_writes_config_outputs(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg = PipelineConfig(
        event_state_path=tmp_path / "state.json",
        ranked_csv_path=tmp_path / "ranked.csv",
        summary_md_path=tmp_path / "summary.md",
        structure_map_path=tmp_path / "structure_map.md",
    )
    brief = (
        "Event type: lunch\n"
        "People we want: engineers\n"
        "Goal: morale\n"
    )
    code, meta = run_pipeline(brief, config=cfg, brief_source_label="test", quiet=True)
    assert code == 0
    assert (tmp_path / "state.json").exists()
    assert (tmp_path / "ranked.csv").exists()
    assert meta["ranked_count"] >= 0


def test_post_run_rejects_empty_body():
    from apps.api.main import app

    client = TestClient(app)
    r = client.post("/run", json={"brief_text": ""})
    assert r.status_code == 422


def test_post_run_returns_summary(monkeypatch):
    import packages.agents.run_intelligence as ri

    def fake_run_pipeline(*args, **kwargs):
        return 0, {
            "event_state_path": "/tmp/state.json",
            "ranked_people_csv_path": "/tmp/ranked.csv",
            "intelligence_summary_path": "/tmp/summary.md",
            "structure_map_path": "/tmp/map.md",
            "ranked_count": 0,
            "high_priority_count": 0,
            "top_gap_persona": None,
            "db_status": "skipped",
            "files_written": [],
        }

    monkeypatch.setattr(ri, "run_pipeline", fake_run_pipeline)

    from apps.api.main import app

    client = TestClient(app)
    r = client.post("/run", json={"brief_text": "Event type: x\nPeople we want: y\nGoal: z\n"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("ok") is True
    assert body.get("ranked_count") == 0
