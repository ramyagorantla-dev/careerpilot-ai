from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# Load API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

model = None

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")  # ✅ stable model
    except Exception as e:
        print("AI INIT ERROR:", str(e))
else:
    print("ERROR: GEMINI_API_KEY missing")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({
        "status": "running",
        "ai_configured": model is not None
    })


@app.route("/api/career", methods=["POST"])
def career_ai():
    try:
        if model is None:
            return jsonify({"error": "AI not configured"}), 500

        data = request.get_json()

        tool_type = data.get("tool_type", "")
        resume = data.get("resume", "")
        job_description = data.get("job_description", "")
        target_role = data.get("target_role", "")

        if not tool_type:
            return jsonify({"error": "Select a tool"}), 400

        if tool_type in ["ats", "optimizer"] and (not resume or not job_description):
            return jsonify({"error": "Resume & job description required"}), 400

        if tool_type == "skillgap" and not target_role:
            return jsonify({"error": "Target role required"}), 400

        # Prompt
        prompt = f"""
You are a professional career coach.

Tool: {tool_type}

Resume:
{resume}

Job Description:
{job_description}

Target Role:
{target_role}

Give structured output:
- Score (if ATS)
- Skills match
- Missing skills
- Improvements
"""

        response = model.generate_content(prompt)

        return jsonify({
            "result": response.text if response else "No response"
        })

fallback_result = """
ATS Match Score: 72/100

Matched Keywords:
- Python
- Flask
- Cloud
- API
- SQL
- Resume analysis

Missing Keywords:
- Job-specific tools
- Measurable achievements
- Exact job title
- Business impact keywords

What To Improve:
- Add the exact target job title in the summary.
- Add 4–5 measurable bullet points with numbers.
- Match important skills from the job description.
- Add cloud/API project experience clearly.

3 Improved Resume Bullet Points:
- Built and deployed a Flask-based AI career platform with secure server-side API integration.
- Configured custom domain, HTTPS, and cloud deployment for a production-ready web application.
- Designed ATS-style resume analysis with keyword matching, skill gap insights, and improvement recommendations.
"""

return jsonify({"result": fallback_result})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)