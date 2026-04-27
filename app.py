from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

app = Flask(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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

        if not tool_type:
            return jsonify({"error": "Please select a tool."}), 400

        if tool_type in ["ats", "optimizer"] and (not resume or not job_description):
            return jsonify({"error": "Please paste both resume and job description."}), 400

        if tool_type == "skillgap" and not target_role:
            return jsonify({"error": "Please enter your target role."}), 400

        system_prompt = """
        You are CareerPilot AI, an expert technical recruiter, ATS resume reviewer,
        career coach, and skill-gap advisor.

        Give practical, honest, structured career guidance.
        Do not give generic advice.
        Use the user's resume, job description, and target role carefully.
        Format the answer with clear headings and bullet points.
        """

        if tool_type == "ats":
            user_prompt = f"""
            Analyze this resume against the job description.

            Resume:
            {resume}

            Job Description:
            {job_description}

            Provide:
            1. ATS Match Score out of 100
            2. Strong matching keywords
            3. Missing keywords or skills
            4. Weak resume areas
            5. Exact improvement suggestions
            6. 3 rewritten resume bullet examples
            """

        elif tool_type == "optimizer":
            user_prompt = f"""
            Optimize this job application.

            Resume:
            {resume}

            Job Description:
            {job_description}

            Provide:
            1. Why this resume may be rejected
            2. What to add or remove
            3. Improved professional summary
            4. Skills section improvements
            5. Experience section improvements
            6. Likely interview questions
            """

        else:
            user_prompt = f"""
            Create a skill gap analysis and roadmap.

            Target Role:
            {target_role}

            Current Resume or Skills:
            {resume}

            Provide:
            1. Required skills for the role
            2. Skills the user already has
            3. Missing skills
            4. 30-day learning roadmap
            5. 3 project ideas to close the gap
            6. Interview preparation topics
            """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4
        )

        result = response.choices[0].message.content
        return jsonify({"result": result})

    except Exception:
        return jsonify({
            "error": "AI service is temporarily unavailable. Please try again later."
        }), 500


if __name__ == "__main__":
    app.run(debug=True)