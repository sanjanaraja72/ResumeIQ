import json
import os
import re
from urllib.parse import quote_plus

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from utils.parser import extract_contact

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(BASE, "data", "skills.json"), encoding="utf-8") as f:
    SKILLS = json.load(f)
with open(os.path.join(BASE, "data", "job_roles.json"), encoding="utf-8") as f:
    ROLES = json.load(f)

ALIASES = {
    "js": "JavaScript", "nodejs": "Node.js", "node": "Node.js", "reactjs": "React",
    "ml": "Machine Learning", "dl": "Deep Learning", "sklearn": "Scikit-learn",
    "scikit learn": "Scikit-learn", "powerbi": "Power BI", "springboot": "Spring Boot",
    "tailwind": "Tailwind CSS", "natural language processing": "NLP",
    "rest apis": "REST API", "restful": "REST API", "postgres": "PostgreSQL",
    "mongo": "MongoDB", "k8s": "Kubernetes", "html5": "HTML", "css3": "CSS",
    "ms excel": "Excel", "microsoft excel": "Excel",
}
CASE_SENSITIVE = {"C", "R", "Go"}
ACTION_VERBS = ["developed", "built", "designed", "implemented", "created", "led",
                "managed", "improved", "optimized", "analyzed", "deployed", "automated"]
SECTIONS = {
    "Summary": r"summary|objective|profile|about",
    "Education": r"education|academic",
    "Skills": r"skills|technologies|technical",
    "Projects": r"projects?",
    "Experience": r"experience|internship|work history",
    "Certifications": r"certifications?|courses?|achievements",
}


def _pattern(term, case_sensitive=False):
    body = re.escape(term).replace(r"\ ", r"\s+")
    return re.compile(r"(?<![A-Za-z0-9+#])" + body + r"(?![A-Za-z0-9+#])",
                      0 if case_sensitive else re.I)


# Compile once
_PATTERNS = []
for cat, items in SKILLS.items():
    for s in items:
        _PATTERNS.append((s, cat, _pattern(s, s in CASE_SENSITIVE)))
_ALIAS_PATTERNS = [(skill, _pattern(a)) for a, skill in ALIASES.items()]
_CAT_OF = {s: c for s, c, _ in _PATTERNS}


def extract_skills(text):
    found = set()
    for skill, _, pat in _PATTERNS:
        if pat.search(text):
            found.add(skill)
    for skill, pat in _ALIAS_PATTERNS:
        if pat.search(text):
            found.add(skill)
    return found


def group_by_category(skills):
    grouped = {}
    for s in sorted(skills):
        grouped.setdefault(_CAT_OF.get(s, "Other"), []).append(s)
    return grouped


def ats_score(text, skills, contact):
    words = len(text.split())
    breakdown = {}

    # 1. Sections (30)
    present = [n for n, p in SECTIONS.items()
               if re.search(r"(?im)^\s*(" + p + r")\b", text)]
    breakdown["Sections"] = round(len(present) / len(SECTIONS) * 30)

    # 2. Contact info (10)
    c = sum(1 for k in ("email", "phone", "linkedin", "github") if contact.get(k))
    breakdown["Contact Info"] = min(10, round(c / 3 * 10))

    # 3. Skills (30)
    breakdown["Skills"] = round(min(len(skills) / 15, 1) * 30)

    # 4. Impact: action verbs + numbers (20)
    verbs = sum(1 for v in ACTION_VERBS if re.search(r"\b" + v + r"\b", text, re.I))
    nums = len(re.findall(r"\d+%|\d+\+|\b\d{2,}\b", text))
    breakdown["Impact"] = round(min(verbs / 5, 1) * 10 + min(nums / 5, 1) * 10)

    # 5. Length (10)
    if 250 <= words <= 900:
        breakdown["Length"] = 10
    elif 150 <= words < 250 or 900 < words <= 1200:
        breakdown["Length"] = 5
    else:
        breakdown["Length"] = 2

    total = min(100, sum(breakdown.values()))
    missing_sections = [n for n in SECTIONS if n not in present]
    return total, breakdown, missing_sections, verbs, nums, words


def role_matches(skills):
    out = []
    for role, req in ROLES.items():
        have = [s for s in req if s in skills]
        miss = [s for s in req if s not in skills]
        out.append({"role": role, "match": round(len(have) / len(req) * 100),
                    "have": have, "missing": miss})
    return sorted(out, key=lambda x: x["match"], reverse=True)


def learn_link(skill):
    q = quote_plus(f"{skill} tutorial for beginners")
    return f"https://www.youtube.com/results?search_query={q}"


def analyze_resume(text):
    contact = extract_contact(text)
    skills = extract_skills(text)
    score, breakdown, miss_sec, verbs, nums, words = ats_score(text, skills, contact)
    roles = role_matches(skills)
    best = roles[0]

    recs = [{"skill": s, "priority": "High" if i < 3 else "Medium", "link": learn_link(s)}
            for i, s in enumerate(best["missing"])]

    tips = []
    for s in miss_sec:
        tips.append(f"Add a '{s}' section to your resume.")
    if nums < 3:
        tips.append("Add numbers/results (e.g., 'improved accuracy by 15%').")
    if verbs < 4:
        tips.append("Start bullet points with action verbs like Developed, Built, Implemented.")
    if not contact.get("linkedin"):
        tips.append("Add your LinkedIn profile link.")
    if not contact.get("github"):
        tips.append("Add your GitHub link to show projects.")
    if words < 250:
        tips.append("Resume is too short. Add more project details.")
    if words > 900:
        tips.append("Resume is too long. Keep it to 1 page.")

    return {
        "contact": contact,
        "skills": group_by_category(skills),
        "skill_count": len(skills),
        "ats_score": score,
        "breakdown": breakdown,
        "roles": roles[:5],
        "best_role": best,
        "recommendations": recs,
        "tips": tips,
        "word_count": words,
    }


def match_with_jd(resume_text, jd_text):
    r_sk, j_sk = extract_skills(resume_text), extract_skills(jd_text)
    overlap = r_sk & j_sk
    skill_pct = len(overlap) / len(j_sk) if j_sk else 0
    try:
        tfidf = TfidfVectorizer(stop_words="english").fit_transform([resume_text, jd_text])
        cos = float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])
    except ValueError:
        cos = 0
    final = round((0.6 * skill_pct + 0.4 * cos) * 100)
    return {
        "match": final,
        "matched": sorted(overlap),
        "missing": sorted(j_sk - r_sk),
    }