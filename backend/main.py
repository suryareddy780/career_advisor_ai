import os
import re
import json
import sqlite3
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="Career Advisor AI — Responsible & Unbiased Career Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "career_advisor.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS advisor_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_name TEXT,
            skills TEXT NOT NULL,
            experience_years REAL NOT NULL,
            interests TEXT NOT NULL,
            suggested_roles TEXT NOT NULL,
            roadmap_json TEXT NOT NULL,
            safety_report_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


init_db()


class UserProfile(BaseModel):
    candidate_name: Optional[str] = "Candidate"
    skills: List[str]
    experience_years: float
    interests: List[str]
    raw_bio: Optional[str] = ""


# --- Responsible AI Guardrails: Bias & Safety Filter ---
PROTECTED_ATTRIBUTE_PATTERNS = [
    r"\b(male|female|man|woman|gender|boy|girl|non-binary)\b",
    r"\b(age|years old|born in 19\d\d|born in 20\d\d|elderly|young)\b",
    r"\b(religion|christian|muslim|hindu|jewish|sikh|atheist)\b",
    r"\b(race|ethnicity|caste|nationality|married|single|pregnant|disability)\b",
]

UNSAFE_INTENT_PATTERNS = [
    r"\b(fake resume|forge|falsify|lie on cv|illegal|fraud|cheat|plagiarize)\b",
    r"\b(discriminate|exclude women|only hire men|no older workers)\b",
]


def run_responsible_ai_audit(profile: UserProfile) -> dict:
    """
    1. Checks for unsafe/unethical requests (e.g., resume fraud or discriminatory filtering).
    2. Strips protected demographic attributes from raw_bio so recommendations rely
       strictly on skills, experience, and interests (demographic-blind fairness).
    """
    combined_text = f"{profile.raw_bio} {' '.join(profile.skills)} {' '.join(profile.interests)}".lower()

    for pattern in UNSAFE_INTENT_PATTERNS:
        if re.search(pattern, combined_text):
            raise HTTPException(
                status_code=400,
                detail="Safety Guardrail Triggered: Request contains unethical or discriminatory criteria (e.g., resume falsification or protected-class exclusion)."
            )

    redacted_bio = profile.raw_bio or ""
    stripped_attributes = []
    for pattern in PROTECTED_ATTRIBUTE_PATTERNS:
        matches = re.findall(pattern, redacted_bio, flags=re.IGNORECASE)
        if matches:
            stripped_attributes.extend([m.lower() for m in matches])
            redacted_bio = re.sub(pattern, "[REDACTED_DEMOGRAPHIC]", redacted_bio, flags=re.IGNORECASE)

    return {
        "bias_mitigation_applied": True,
        "demographic_blind_scoring": True,
        "stripped_protected_terms": sorted(list(set(stripped_attributes))),
        "sanitized_bio": redacted_bio.strip(),
        "safety_status": "PASSED — Evaluated strictly on skills, experience & interests",
        "fairness_principles": [
            "Skill-first meritocratic matching (no gender, age, race, or background weighting)",
            "Inclusive, gender-neutral job titles and roadmap language",
            "Transparent match reasoning and verifiable upskilling steps"
        ]
    }


ROLE_CATALOG = [
    {
        "title": "AI / Machine Learning Engineer",
        "required_skills": ["python", "machine learning", "pytorch", "tensorflow", "sql", "nlp", "llm"],
        "min_exp": 1.0,
        "avg_salary_range": "$115,000 - $165,000",
        "roadmap": [
            {"phase": "Weeks 1-4: Foundations", "action": "Master Python data pipelines, NumPy/Pandas, and supervised ML algorithms."},
            {"phase": "Weeks 5-8: Deep Learning & LLMs", "action": "Build and fine-tune Transformer/RAG pipelines with evaluation metrics."},
            {"phase": "Weeks 9-12: Production & Ethics", "action": "Deploy a FastAPI ML microservice with bias auditing, model cards, and CI tests."}
        ]
    },
    {
        "title": "Full-Stack Software Engineer",
        "required_skills": ["python", "javascript", "react", "fastapi", "node", "sql", "git", "html", "css"],
        "min_exp": 0.0,
        "avg_salary_range": "$95,000 - $145,000",
        "roadmap": [
            {"phase": "Weeks 1-4: Backend & APIs", "action": "Design RESTful services with FastAPI/Node, authentication, and relational schemas."},
            {"phase": "Weeks 5-8: Interactive Frontend", "action": "Build accessible, responsive UI components with state management and API integration."},
            {"phase": "Weeks 9-12: Cloud & Testing", "action": "Add automated pytest/Playwright suites, Dockerize, and deploy with CI/CD."}
        ]
    },
    {
        "title": "Data Analyst & BI Specialist",
        "required_skills": ["sql", "excel", "python", "tableau", "power bi", "statistics", "data analysis"],
        "min_exp": 0.0,
        "avg_salary_range": "$75,000 - $115,000",
        "roadmap": [
            {"phase": "Weeks 1-4: Querying & Modeling", "action": "Master advanced SQL window functions, CTEs, and dimensional data modeling."},
            {"phase": "Weeks 5-8: Statistical Storytelling", "action": "Perform A/B test hypothesis analysis and build interactive executive dashboards."},
            {"phase": "Weeks 9-12: Governance & Portfolio", "action": "Document data lineage, privacy compliance (PII handling), and 2 end-to-end case studies."}
        ]
    },
    {
        "title": "AI Product & Responsible AI Specialist",
        "required_skills": ["product management", "ai ethics", "prompt engineering", "user research", "analytics", "llm"],
        "min_exp": 1.0,
        "avg_salary_range": "$105,000 - $155,000",
        "roadmap": [
            {"phase": "Weeks 1-4: AI Evaluation & Prompting", "action": "Design structured prompt rubrics, hallucination benchmarks, and red-teaming tests."},
            {"phase": "Weeks 5-8: Fairness & Compliance", "action": "Implement NIST AI RMF & EU AI Act risk checklists and bias mitigation workflows."},
            {"phase": "Weeks 9-12: End-to-End Launch", "action": "Ship an AI feature MVP with human-in-the-loop feedback and transparent user disclosures."}
        ]
    }
]


def recommend_jobs_and_roadmap(profile: UserProfile, safety_report: dict) -> dict:
    user_skills = {s.strip().lower() for s in profile.skills if s.strip()}
    user_interests = {i.strip().lower() for i in profile.interests if i.strip()}

    scored_roles = []
    for role in ROLE_CATALOG:
        req = set(role["required_skills"])
        matched_skills = sorted(list(user_skills.intersection(req)))
        missing_skills = sorted(list(req - user_skills))

        skill_ratio = len(matched_skills) / max(len(req), 1)
        interest_boost = 0.15 if any(k in role["title"].lower() for k in user_interests) else 0.0
        exp_factor = 0.15 if profile.experience_years >= role["min_exp"] else 0.05

        match_score = min(round((skill_ratio * 0.70 + interest_boost + exp_factor) * 100, 1), 98.0)
        scored_roles.append({
            "title": role["title"],
            "match_score": match_score,
            "avg_salary_range": role["avg_salary_range"],
            "matched_skills": matched_skills,
            "skill_gaps_to_learn": missing_skills[:4],
            "why_recommended": f"Matches {len(matched_skills)}/{len(req)} core competencies based purely on verified skills and {profile.experience_years} yrs experience.",
            "roadmap": role["roadmap"]
        })

    scored_roles.sort(key=lambda x: x["match_score"], reverse=True)
    top_roles = scored_roles[:3]
    primary_roadmap = top_roles[0]["roadmap"]

    return {
        "candidate_name": profile.candidate_name or "Candidate",
        "suggested_jobs": top_roles,
        "personalized_roadmap": primary_roadmap,
        "responsible_ai_audit": safety_report
    }


@app.get("/")
def serve_ui():
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    return FileResponse(frontend_path)


@app.post("/api/advise")
def generate_career_advice(profile: UserProfile):
    if not profile.skills:
        raise HTTPException(status_code=422, detail="At least one skill is required.")

    safety_report = run_responsible_ai_audit(profile)
    result = recommend_jobs_and_roadmap(profile, safety_report)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    cursor.execute(
        """
        INSERT INTO advisor_sessions (
            candidate_name, skills, experience_years, interests,
            suggested_roles, roadmap_json, safety_report_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            result["candidate_name"],
            json.dumps(profile.skills),
            profile.experience_years,
            json.dumps(profile.interests),
            json.dumps(result["suggested_jobs"]),
            json.dumps(result["personalized_roadmap"]),
            json.dumps(safety_report),
            now,
        ),
    )
    result["session_id"] = cursor.lastrowid
    result["created_at"] = now
    conn.commit()
    conn.close()
    return result


@app.get("/api/sessions")
def list_sessions():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, candidate_name, skills, experience_years, created_at FROM advisor_sessions ORDER BY id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows
