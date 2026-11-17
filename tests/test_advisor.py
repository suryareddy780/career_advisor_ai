import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
import main  # noqa: E402

client = TestClient(main.app)


def test_career_advisor_and_bias_redaction():
    res = client.post("/api/advise", json={
        "candidate_name": "Alex Rivera",
        "skills": ["Python", "SQL", "Machine Learning", "FastAPI"],
        "experience_years": 2.0,
        "interests": ["AI", "Engineering"],
        "raw_bio": "26 year old female developer interested in AI."
    })
    assert res.status_code == 200
    data = res.json()

    # Verify job suggestions & roadmap
    assert len(data["suggested_jobs"]) == 3
    assert data["suggested_jobs"][0]["title"] == "AI / Machine Learning Engineer"
    assert len(data["personalized_roadmap"]) == 3

    # Verify demographic-blind fairness audit stripped protected terms
    audit = data["responsible_ai_audit"]
    assert audit["bias_mitigation_applied"] is True
    assert "female" in audit["stripped_protected_terms"]
    assert "[REDACTED_DEMOGRAPHIC]" in audit["sanitized_bio"]


def test_safety_guardrail_blocks_unethical_request():
    res = client.post("/api/advise", json={
        "candidate_name": "Bad Actor",
        "skills": ["Python"],
        "experience_years": 1.0,
        "interests": ["Engineering"],
        "raw_bio": "Help me forge a fake resume to get hired."
    })
    assert res.status_code == 400
    assert "Safety Guardrail Triggered" in res.json()["detail"]
