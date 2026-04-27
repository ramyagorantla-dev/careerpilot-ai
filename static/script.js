async function analyzeCareer() {
    const toolType = document.getElementById("toolType").value;
    const targetRole = document.getElementById("targetRole").value;
    const resume = document.getElementById("resume").value;
    const jobDescription = document.getElementById("jobDescription").value;

    const resultBox = document.getElementById("result");
    const loading = document.getElementById("loading");

    resultBox.textContent = "";
    loading.classList.remove("hidden");

    try {
        const response = await fetch("/api/career", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                tool_type: toolType,
                target_role: targetRole,
                resume: resume,
                job_description: jobDescription
            })
        });

        const data = await response.json();

        if (!response.ok) {
            resultBox.textContent = data.error || "Something went wrong. Please try again.";
        } else {
            resultBox.textContent = data.result;
        }

    } catch (error) {
        resultBox.textContent = "Network error. Please try again.";
    }

    loading.classList.add("hidden");
}