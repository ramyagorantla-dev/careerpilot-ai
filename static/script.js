console.log("CareerPilot script loaded");
async function analyzeCareer() {
    const toolType = document.getElementById("toolType").value;
    const targetRole = document.getElementById("targetRole").value.trim();
    const resume = document.getElementById("resume").value.trim();
    const jobDescription = document.getElementById("jobDescription").value.trim();

    const resultBox = document.getElementById("result");
    const loading = document.getElementById("loading");

    if (!toolType) {
        alert("Please select a tool.");
        return;
    }

    if ((toolType === "ats" || toolType === "optimizer") && (!resume || !jobDescription)) {
        alert("Please paste resume and job description.");
        return;
    }

    if (toolType === "skillgap" && (!resume || !targetRole)) {
        alert("Please enter resume and target role.");
        return;
    }

    resultBox.innerHTML = "";
    loading.classList.remove("hidden");

    try {
        const response = await fetch("/api/career", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                tool_type: toolType,
                target_role: targetRole,
                resume: resume,
                job_description: jobDescription
            })
        });

        const data = await response.json();

        if (!response.ok) {
            resultBox.innerHTML = `<div class="error-box">${data.error || "Something went wrong."}</div>`;
        } else {
            resultBox.innerHTML = renderReport(data);
        }

    } catch (err) {
        resultBox.innerHTML = `<div class="error-box">Network error. Please try again.</div>`;
    }

    loading.classList.add("hidden");
}


function renderReport(data) {
    if (data.tool_type === "skillgap") {
        return renderSkillGap(data);
    }

    if (data.tool_type === "optimizer") {
        return renderOptimizer(data);
    }

    return renderATS(data);
}


/* =========================
   1. ATS Resume Checker
   Diagnosis View
========================= */
function renderATS(data) {
    const r = data.report;

    return `
        <div class="report-layout">

            ${renderSidebar(r)}

            <div class="scan-main">

                <div class="scan-header">
                    <div>
                        <small>ATS Resume Checker</small>
                        <h2>${r.job_title}</h2>
                    </div>
                    <button class="print-btn" onclick="window.print()">Print</button>
                </div>

                <div class="scan-tabs">
                    <div class="active-tab">Resume Report</div>
                    <div>Job Description Match</div>
                </div>

                <div class="ats-tip">
                    <strong>ATS Tip</strong>
                    <span>Add the exact job title and important tools from the job description if they honestly match your background.</span>
                </div>

                <div class="analysis-section">
                    <h2>Searchability</h2>
                    <p>This checks whether your resume can be read and searched by ATS systems and recruiters.</p>
                    ${renderChecks(r.checks)}
                </div>

                <div class="analysis-section">
                    <h2>Hard Skills Comparison</h2>
                    <p>These are job-related keywords found in the job description and compared with your resume.</p>
                    ${renderSkillTable(r.skill_rows)}
                </div>

                <div class="analysis-section">
                    <h2>Boost Your Match Rate</h2>
                    <div class="boost-box">
                        <p><strong>Current Score:</strong> ${r.score}%</p>
                        <p><strong>Possible After Improvements:</strong> ${r.boost_score}%</p>
                        <p>Add stronger role keywords, measurable achievements, and the target job title if accurate.</p>
                    </div>
                </div>

                <div class="analysis-section">
                    <h2>AI Recommendations</h2>
                    <div class="ai-box">
                        ${formatAI(data.ai_text)}
                    </div>
                </div>

            </div>
        </div>
    `;
}


/* =========================
   2. Job Application Optimizer
   Action Plan View
========================= */
function renderOptimizer(data) {
    const r = data.report;

    return `
        <div class="optimizer-layout">

            <div class="optimizer-hero">
                <div>
                    <small>Job Application Optimizer</small>
                    <h2>Turn your resume into a stronger application</h2>
                    <p>This view focuses on what to change before applying, not just the score.</p>
                </div>

                <div class="optimizer-score">
                    <strong>${r.score}%</strong>
                    <span>Current Match</span>
                </div>
            </div>

            <div class="optimizer-grid">
                <div class="optimizer-card">
                    <h3>Top Keywords to Add</h3>
                    ${renderKeywordChips(r.focus_areas)}
                </div>

                <div class="optimizer-card">
                    <h3>Matched Strengths</h3>
                    ${renderKeywordChips(r.matched_keywords)}
                </div>

                <div class="optimizer-card">
                    <h3>Score Improvement Potential</h3>
                    <p><strong>${r.score}% → ${r.boost_score}%</strong></p>
                    <p>Improve by tailoring summary, skills, and project bullets to the role.</p>
                </div>

                <div class="optimizer-card">
                    <h3>Resume Quality Signals</h3>
                    <p><strong>Word Count:</strong> ${r.word_count}</p>
                    <p><strong>Measurable Results:</strong> ${r.metrics}</p>
                </div>
            </div>

            <div class="analysis-section optimizer-section">
                <h2>Application Action Plan</h2>
                <div class="ai-box">
                    ${formatAI(data.ai_text)}
                </div>
            </div>

            <div class="analysis-section optimizer-section">
                <h2>Skills Comparison</h2>
                ${renderSkillTable(r.skill_rows)}
            </div>
        </div>
    `;
}


/* =========================
   3. Skill Gap Analyzer
   Learning Roadmap View
========================= */
function renderSkillGap(data) {
    return `
        <div class="roadmap-layout">

            <div class="roadmap-hero">
                <small>Skill Gap Analyzer</small>
                <h2>Personalized Career Roadmap</h2>
                <p>This view helps students understand what to learn next, what to build, and how to prepare.</p>
            </div>

            <div class="roadmap-card">
                ${formatAI(data.ai_text)}
            </div>

        </div>
    `;
}


/* =========================
   Shared Components
========================= */
function renderSidebar(r) {
    return `
        <div class="scan-sidebar">

            <div class="circle-score">
                <div class="circle-inner">
                    <strong>${r.score}%</strong>
                    <span>Match Rate</span>
                </div>
            </div>

            ${metric("Searchability", r.categories.searchability)}
            ${metric("Hard Skills", r.categories.hard_skills)}
            ${metric("Soft Skills", r.categories.soft_skills)}
            ${metric("Recruiter Tips", r.categories.recruiter_tips)}
            ${metric("Formatting", r.categories.formatting)}

        </div>
    `;
}


function metric(title, data) {
    return `
        <div class="side-metric">
            <div class="metric-row">
                <span>${title}</span>
                <small>${data.issues} issue${data.issues === 1 ? "" : "s"}</small>
            </div>
            <div class="metric-bar">
                <div style="width:${data.score}%"></div>
            </div>
        </div>
    `;
}


function renderChecks(sections) {
    return sections.map(section => `
        <div class="check-card">
            <div class="check-row">
                <div class="check-title">${section.section}</div>
                <div class="check-items">
                    ${section.items.map(item => `
                        <div class="check-item">
                            <span class="${item.ok ? "ok" : "bad"}">
                                ${item.ok ? "✔" : "✖"}
                            </span>
                            <span>${item.text}</span>
                        </div>
                    `).join("")}
                </div>
            </div>
        </div>
    `).join("");
}


function renderSkillTable(rows) {
    return `
        <div class="skills-table">
            <div class="table-head">
                <div>Skill</div>
                <div>Resume</div>
                <div>Job Description</div>
            </div>

            ${rows.map(row => `
                <div class="table-row">
                    <div>${row.skill}</div>
                    <div>${row.resume_count > 0 ? row.resume_count : "<span class='bad-text'>×</span>"}</div>
                    <div>${row.job_count}</div>
                </div>
            `).join("")}
        </div>
    `;
}


function renderKeywordChips(keywords) {
    if (!keywords || keywords.length === 0) {
        return `<p>No keywords detected.</p>`;
    }

    return `
        <div class="chip-wrap">
            ${keywords.slice(0, 12).map(keyword => `
                <span class="keyword-chip">${keyword}</span>
            `).join("")}
        </div>
    `;
}


function formatAI(text) {
    if (!text) return "No response available.";

    let formatted = text
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/What To Improve:/g, "<h3>What To Improve</h3>")
        .replace(/What To Learn Next:/g, "<h3>What To Learn Next</h3>")
        .replace(/Free Resources:/g, "<h3>Free Resources</h3>")
        .replace(/3 Resume Bullet Improvements:/g, "<h3>Resume Bullet Improvements</h3>")
        .replace(/Current Strengths:/g, "<h3>Current Strengths</h3>")
        .replace(/8 Week Learning Plan:/g, "<h3>8 Week Learning Plan</h3>")
        .replace(/Real Project To Build:/g, "<h3>Real Project To Build</h3>")
        .replace(/Interview Preparation:/g, "<h3>Interview Preparation</h3>")
        .replace(/\n- /g, "<br><span class='bullet'>•</span> ")
        .replace(/\n\* /g, "<br><span class='bullet'>•</span> ")
        .replace(/\n/g, "<br>");

    return formatted;
}