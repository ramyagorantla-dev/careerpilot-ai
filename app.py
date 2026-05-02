from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# Load API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("ERROR: GEMINI_API_KEY not found")
else:
    genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.0-flash")  # stable model


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
        data = request.get_json()

        tool_type = data.get("tool_type", "")
        resume = data.get("resume", "")
        job_description = data.get("job_description", "")
        target_role = data.get("target_role", "")

        if not tool_type:
            return jsonify({"error": "Please select a tool."}), 400

        if tool_type in ["ats", "optimizer"] and (not resume or not job_description):
            return jsonify({"error": "Resume & job description required."}), 400

        if tool_type == "skillgap" and not target_role:
            return jsonify({"error": "Target role required."}), 400

        system_prompt = """
        You are CareerPilot AI, an expert recruiter and career coach.
        Give structured, realistic, actionable advice.
        """

        if tool_type == "ats":
            user_prompt = f"""
            Analyze resume vs job description.

            Resume:
            {resume}

            Job:
            {job_description}

            Give:
            - ATS score (0-100)
            - Matching skills
            - Missing skills
            - Improvements
            """

        elif tool_type == "optimizer":
            user_prompt = f"""
            Improve this application:

            Resume:
            {resume}

            Job:
            {job_description}
            """

        else:
            user_prompt = f"""
            Skill gap roadmap:

            Role: {target_role}
            Current: {resume}
            """

        final_prompt = system_prompt + "\n\n" + user_prompt

        response = model.generate_content(final_prompt)

        return jsonify({"result": response.text})

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({
            "error": "AI temporarily unavailable"
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)