from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# Load Gemini API Key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in environment variables")

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")


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

        # Validation
        if not tool_type:
            return jsonify({"error": "Please select a tool."}), 400

        if tool_type in ["ats", "optimizer"] and (not resume or not job_description):
            return jsonify({"error": "Please paste both resume and job description."}), 400

        if tool_type == "skillgap" and not target_role:
            return jsonify({"error": "Please enter your target role."}), 400

        # System Prompt
        system_prompt = """
        You are CareerPilot AI, an expert technical recruiter, ATS resume reviewer,
        career coach, and skill-gap advisor.

        Give practical, structured, real-world advice.
        Avoid generic answers.
        Use clear headings and bullet points.
        """

        # Tool Logic
        if tool_type == "ats":
            user_prompt = f"""
            Analyze resume vs job description.

            Resume:
            {resume}

            Job Description:
            {job_description}

            Provide:
            - ATS Match Score (0–100)
            - Matching keywords
            - Missing keywords
            - Weak areas
            - Improvements
            - 3 improved resume bullets
            """

        elif tool_type == "optimizer":
            user_prompt = f"""
            Improve this job application.

            Resume:
            {resume}

            Job Description:
            {job_description}

            Provide:
            - Why it may get rejected
            - What to add/remove
            - Improved summary
            - Skills improvements
            - Experience improvements
            - Interview questions
            """

        else:  # skillgap
            user_prompt = f"""
            Create a skill gap roadmap.

            Target Role:
            {target_role}

            Current Skills:
            {resume}

            Provide:
            - Required skills
            - Current strengths
            - Missing skills
            - 30-day roadmap
            - 3 project ideas
            - Interview topics
            """

        final_prompt = system_prompt + "\n\n" + user_prompt

        response = model.generate_content(final_prompt)

        return jsonify({"result": response.text})

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({
            "error": "AI service is temporarily unavailable. Please try again."
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
