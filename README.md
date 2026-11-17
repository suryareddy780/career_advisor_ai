# Career Advisor AI — Responsible & Unbiased Career Assistant

An end-to-end AI assistant combining **User Profile Analysis**, **Merit-Based Job Recommendations**, **12-Week Upskilling Roadmaps**, and **Responsible AI Bias & Safety Guardrails**.

## Key Features
1. **Profile Evaluation**: Analyzes verified skills, years of experience, and career interests.
2. **Job Matching Engine**: Scores and ranks roles with transparent skill-match percentages and skill-gap breakdowns.
3. **Personalized 12-Week Roadmap**: Generates phased action steps from foundations to production deployment.
4. **Responsible AI Guardrails**:
   - **Demographic-Blind Redaction**: Strips age, gender, religion, race, and marital status terms before scoring.
   - **Safety Intent Filter**: Blocks unethical requests (e.g., resume falsification or discriminatory filtering).

## Quickstart
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
Open `http://127.0.0.1:8000` in your browser.

## Run Tests
```bash
pytest -v
```
