from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai
import os
import re
from collections import Counter

load_dotenv()

app = Flask(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("ERROR: GEMINI_API_KEY is missing in .env file")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")


COMMON_WORDS = {
    "the", "and", "for", "with", "that", "this", "you", "your", "are", "will",
    "from", "our", "they", "their", "have", "has", "was", "were", "can", "but",
    "not", "all", "any", "job", "role", "work", "team", "using", "use", "used",
    "experience", "skills", "ability", "knowledge", "required", "preferred",
    "responsibilities", "requirements", "candidate", "company", "including",
    "such", "etc", "based", "strong", "good", "excellent", "plus", "must"
}

HARD_SKILLS = {
    "python", "java", "javascript", "typescript", "html", "css", "sql", "mssql",
    "mysql", "oracle", "as400", "flask", "django", "react", "node", "aws",
    "azure", "gcp", "cloud", "ec2", "s3", "iam", "lambda", "docker",
    "kubernetes", "linux", "nginx", "api", "apis", "rest", "sap", "cpi",
    "btp", "data", "analytics", "etl", "migration", "reporting", "jira",
    "git", "github", "excel", "tableau", "powerbi"
}

SOFT_SKILLS = {
    "communication", "leadership", "collaboration", "teamwork", "organization",
    "organized", "detail", "problem", "solving", "analytical", "client",
    "customer", "documentation", "presentation"
}

ACTION_WORDS = {
    "developed", "built", "created", "implemented", "designed", "deployed",
    "automated", "integrated", "optimized", "improved", "managed", "configured",
    "analyzed", "tested", "resolved", "collaborated", "supported", "documented"
}


def clean_text(text):
    return re.sub(r"[^a-zA-Z0-9+#./ ]", " ", text.lower())


def tokenize(text):
    words = clean_text(text).split()
    return [w for w in words if len(w) > 2 and w not in COMMON_WORDS]


def count_word(text, word):
    return clean_text(text).split().count(word.lower())


def extract_keywords(text, top_n=35):
    words = tokenize(text)
    counts = Counter(words)
    boosted = {}

    for word, count in counts.items():
        score = count
        if word in HARD_SKILLS:
            score += 6
        if word in SOFT_SKILLS:
            score += 3
        boosted[word] = score

    sorted_words = sorted(boosted.items(), key=lambda x: x[1], reverse=True)
    return [word for word, score in sorted_words[:top_n]]


def has_email(text):
    return bool(re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text))


def has_phone(text):
    return bool(re.search(r"(\+?\d[\d\s\-\(\)]{8,}\d)", text))


def has_location(text):
    location_words = ["address", "city", "state", "nj", "ny", "pa", "usa", "united states"]
    return any(w in clean_text(text) for w in location_words)


def has_section(text, section_names):
    text_l = clean_text(text)
    return any(section in text_l for section in section_names)


def measurable_count(text):
    patterns = [
        r"\d+%",
        r"\$\d+",
        r"\d+\+",
        r"\d+\s*(years|months|users|requests|projects|clients|systems|apis)"
    ]
    return sum(len(re.findall(p, clean_text(text))) for p in patterns)


def detect_job_title(job_description):
    text = job_description.lower()
    titles = [
        "data analyst", "software engineer", "cloud engineer", "business analyst",
        "systems analyst", "sap developer", "integration developer", "ai developer",
        "product manager", "developer", "analyst", "engineer", "intern"
    ]

    for title in titles:
        if title in text:
            return title.title()

    return "Target Role"


def build_report(resume, job_description):
    resume_clean = clean_text(resume)
    jd_keywords = extract_keywords(job_description, 35)

    skill_rows = []
    matched = []
    focus = []

    for skill in jd_keywords:
        r_count = count_word(resume, skill)
        j_count = count_word(job_description, skill)

        if r_count > 0:
            matched.append(skill)
        else:
            focus.append(skill)

        skill_rows.append({
            "skill": skill.title(),
            "resume_count": r_count,
            "job_count": j_count
        })

    hard_jd = [s for s in jd_keywords if s in HARD_SKILLS]
    hard_matched = [s for s in hard_jd if s in resume_clean]

    soft_jd = [s for s in jd_keywords if s in SOFT_SKILLS]
    soft_matched = [s for s in soft_jd if s in resume_clean]

    keyword_score = round((len(matched) / len(jd_keywords)) * 35) if jd_keywords else 0
    hard_score = round((len(hard_matched) / len(hard_jd)) * 25) if hard_jd else 10
    soft_score = round((len(soft_matched) / len(soft_jd)) * 10) if soft_jd else 6

    email_ok = has_email(resume)
    phone_ok = has_phone(resume)
    location_ok = has_location(resume)

    summary_ok = has_section(resume, ["summary", "professional summary", "profile"])
    education_ok = has_section(resume, ["education", "university", "degree", "bachelor", "master"])
    experience_ok = has_section(resume, ["experience", "work history", "professional experience"])
    skills_ok = has_section(resume, ["skills", "technical skills"])

    formatting_score = 0
    formatting_score += 3 if email_ok else 0
    formatting_score += 3 if phone_ok else 0
    formatting_score += 2 if summary_ok else 0
    formatting_score += 2 if education_ok else 0
    formatting_score += 2 if experience_ok else 0
    formatting_score += 2 if skills_ok else 0

    metrics = measurable_count(resume)
    metric_score = min(metrics * 2, 8)

    action_count = sum(1 for w in ACTION_WORDS if w in resume_clean)
    action_score = min(action_count * 2, 8)

    word_count = len(tokenize(resume))
    word_score = 4 if word_count >= 250 else 2 if word_count >= 120 else 0

    job_title = detect_job_title(job_description)
    job_title_match = job_title.lower() in resume_clean

    total = keyword_score + hard_score + soft_score + formatting_score + metric_score + action_score + word_score
    total = min(total, 100)

    boost_score = min(total + 18, 95)

    categories = {
        "searchability": {
            "score": min(formatting_score * 7, 100),
            "issues": sum([not email_ok, not phone_ok, not location_ok, not summary_ok])
        },
        "hard_skills": {
            "score": round((len(hard_matched) / len(hard_jd)) * 100) if hard_jd else 60,
            "issues": max(len(hard_jd) - len(hard_matched), 0)
        },
        "soft_skills": {
            "score": round((len(soft_matched) / len(soft_jd)) * 100) if soft_jd else 60,
            "issues": max(len(soft_jd) - len(soft_matched), 0)
        },
        "recruiter_tips": {
            "score": 80 if metrics >= 5 else 60 if metrics >= 2 else 40,
            "issues": max(5 - metrics, 0)
        },
        "formatting": {
            "score": min(formatting_score * 7, 100),
            "issues": sum([not summary_ok, not education_ok, not experience_ok, not skills_ok])
        }
    }

    checks = [
        {
            "section": "Contact Information",
            "items": [
                {"ok": location_ok, "text": "Location found." if location_ok else "Add city/state or location availability."},
                {"ok": email_ok, "text": "Email found." if email_ok else "Add a professional email address."},
                {"ok": phone_ok, "text": "Phone number found." if phone_ok else "Add a phone number."}
            ]
        },
        {
            "section": "Summary",
            "items": [
                {"ok": summary_ok, "text": "Summary section found." if summary_ok else "Add a 2–3 line summary using the target role title."}
            ]
        },
        {
            "section": "Section Headings",
            "items": [
                {"ok": education_ok, "text": "Education section found." if education_ok else "Add an Education section."},
                {"ok": experience_ok, "text": "Experience section found." if experience_ok else "Add Experience or Projects section."},
                {"ok": skills_ok, "text": "Skills section found." if skills_ok else "Add a clear Technical Skills section."}
            ]
        },
        {
            "section": "Job Title Match",
            "items": [
                {"ok": job_title_match, "text": f"Target title '{job_title}' found." if job_title_match else f"Add '{job_title}' naturally in your summary if accurate."}
            ]
        },
        {
            "section": "Measurable Results",
            "items": [
                {"ok": metrics >= 5, "text": f"Found {metrics} measurable result(s). Add more numbers, percentages, or impact metrics."}
            ]
        },
        {
            "section": "Word Count",
            "items": [
                {"ok": word_count >= 250, "text": f"Resume has about {word_count} meaningful words. Add relevant project/experience detail if too short."}
            ]
        }
    ]

    return {
        "score": total,
        "boost_score": boost_score,
        "matched_keywords": matched[:15],
        "focus_areas": focus[:15],
        "skill_rows": skill_rows[:18],
        "categories": categories,
        "checks": checks,
        "job_title": job_title,
        "word_count": word_count,
        "metrics": metrics
    }


def fallback_ai_text(report):
    if not report:
        return """
AI recommendations are temporarily unavailable.

Please try again shortly.
"""

    focus = ", ".join(report["focus_areas"][:8]) if report["focus_areas"] else "role-specific keywords"

    return f"""
What To Improve:
- Add the target job title naturally in your summary if it matches your goal.
- Add more measurable results using numbers, percentages, or project impact.
- Strengthen your skills section using keywords from the job description.
- Focus especially on: {focus}.

What To Learn Next:
- Study the tools and skills that appear in the job description but are not strongly shown in your resume.
- Build one small project that proves those skills.

Free Resources:
- freeCodeCamp YouTube tutorials
- Google/Coursera free audit courses
- AWS Skill Builder free content
- Microsoft Learn
- W3Schools / GeeksforGeeks for quick practice

3 Resume Bullet Improvements:
- Developed and documented technical workflows to improve process efficiency and reduce manual effort.
- Built a role-focused project using tools from the job description and published it on GitHub.
- Collaborated with teams to analyze requirements, resolve issues, and deliver measurable outcomes.
"""


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/career", methods=["POST"])
def career_ai():
    try:
        data = request.get_json()

        tool_type = data.get("tool_type", "")
        resume = data.get("resume", "")
        job_description = data.get("job_description", "")
        target_role = data.get("target_role", "")

        if tool_type in ["ats", "optimizer"] and (not resume or not job_description):
            return jsonify({"error": "Please paste both resume and job description."}), 400

        if tool_type == "skillgap" and (not resume or not target_role):
            return jsonify({"error": "Please paste resume/skills and target role."}), 400

        report = build_report(resume, job_description) if tool_type in ["ats", "optimizer"] else None

        if tool_type in ["ats", "optimizer"]:
            prompt = f"""
You are CareerPilot AI. Use the calculated report below. Do not change the score.

Score: {report["score"]}/100
Possible Boost Score: {report["boost_score"]}/100
Matched Keywords: {", ".join(report["matched_keywords"])}
Focus Areas: {", ".join(report["focus_areas"])}
Job Title: {report["job_title"]}

Give concise practical advice in this format:

What To Improve:
-

What To Learn Next:
-

Free Resources:
-

3 Resume Bullet Improvements:
-
"""
        else:
            prompt = f"""
Target Role: {target_role}
Current Resume/Skills: {resume}

Create a positive student roadmap. Do not use the phrase missing skills.

Return:
Current Strengths:
-
What To Learn Next:
-
8 Week Learning Plan:
-
Free Resources:
-
Real Project To Build:
-
Interview Preparation:
-
"""

        try:
            generation_config = genai.GenerationConfig(
                temperature=0.0,
                top_p=0.1,
                top_k=1,
                max_output_tokens=1200
            )

            response = model.generate_content(prompt, generation_config=generation_config)
            ai_text = response.text

        except Exception as ai_error:
            print("AI ERROR:", str(ai_error))
            ai_text = fallback_ai_text(report)

        return jsonify({
            "tool_type": tool_type,
            "report": report,
            "ai_text": ai_text
        })

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": "Something went wrong. Please try again."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)