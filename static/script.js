document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("decisionForm");

    if (!form) {
        console.error("decisionForm not found");
        return;
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const decision = document.getElementById("decision")?.value.trim() || "";
        const goal = document.getElementById("goal")?.value.trim() || "";
        const constraints =
            document.getElementById("constraints")?.value.trim() || "";

        if (decision.length < 10) {
            alert("Please describe your decision in at least 10 characters.");
            return;
        }

        // Find or create result area
        let resultBox = document.getElementById("analysisResult");

        if (!resultBox) {
            resultBox = document.createElement("div");
            resultBox.id = "analysisResult";
            form.parentNode.appendChild(resultBox);
        }

        resultBox.innerHTML = `
            <div class="loading">
                ⚡ Breaking down your decision...<br>
                Finding assumptions • blind spots • risks
            </div>
        `;

        try {
            const formData = new FormData();

            formData.append("decision", decision);
            formData.append("goal", goal);
            formData.append("constraints", constraints);

            const response = await fetch("/analyze", {
                method: "POST",
                body: formData
            });

            const data = await response.json();

            console.log("SERVER RESPONSE:", data);

            if (!response.ok) {
                throw new Error(data.error || "Analysis failed.");
            }

            if (!data.result) {
                throw new Error("No analysis result received.");
            }

            renderAnalysis(data.result, data.mode);

        } catch (error) {
            console.error("ANALYSIS ERROR:", error);

            resultBox.innerHTML = `
                <div class="error">
                    <h3>❌ Analysis failed</h3>
                    <p>${escapeHtml(error.message)}</p>
                    <p>Open the browser console with F12 to see the details.</p>
                </div>
            `;
        }
    });

    function renderAnalysis(result, mode) {
        let resultBox = document.getElementById("analysisResult");

        if (!resultBox) {
            resultBox = document.createElement("div");
            resultBox.id = "analysisResult";
            form.parentNode.appendChild(resultBox);
        }

        const assumptions = Array.isArray(result.assumptions)
            ? result.assumptions
            : [];

        const blindSpots = Array.isArray(result.blind_spots)
            ? result.blind_spots
            : [];

        const risks = Array.isArray(result.risks)
            ? result.risks
            : [];

        const counterarguments = Array.isArray(result.counterarguments)
            ? result.counterarguments
            : [];

        const alternatives = Array.isArray(result.alternatives)
            ? result.alternatives
            : [];

        const evidence = Array.isArray(result.evidence_to_collect)
            ? result.evidence_to_collect
            : [];

        resultBox.innerHTML = `
            <section class="analysis-report">

                <div class="report-header">
                    <h2>🧠 ANALYSIS REPORT</h2>
                    <span class="mode-badge">
                        ${mode === "ai" ? "AI ANALYSIS" : "DEMO ANALYSIS"}
                    </span>
                </div>

                <div class="summary-card">
                    <h3>🎯 Decision Summary</h3>
                    <p>${escapeHtml(result.summary || "No summary available.")}</p>
                </div>

                <div class="metrics">

                    <div class="metric">
                        <strong>${result.confidence ?? "—"}%</strong>
                        <span>Confidence</span>
                    </div>

                    <div class="metric">
                        <strong>${getHighestRisk(risks)}</strong>
                        <span>Highest Risk</span>
                    </div>

                    <div class="metric">
                        <strong>${assumptions.length}</strong>
                        <span>Assumptions</span>
                    </div>

                </div>

                <div class="report-section">
                    <h3>🧠 Hidden Assumptions</h3>

                    ${assumptions.length
                        ? assumptions.map(a => `
                            <div class="analysis-item">
                                <h4>${escapeHtml(a.title || "Assumption")}</h4>
                                <p>${escapeHtml(a.statement || "")}</p>
                                <div class="test">
                                    <strong>Test:</strong>
                                    ${escapeHtml(a.test || "")}
                                </div>
                            </div>
                        `).join("")
                        : "<p>No assumptions returned.</p>"
                    }
                </div>

                <div class="report-section">
                    <h3>🕳️ Blind Spots</h3>

                    <ul>
                        ${blindSpots.map(item =>
                            `<li>${escapeHtml(item)}</li>`
                        ).join("")}
                    </ul>
                </div>

                <div class="report-section">
                    <h3>⚠️ Risk Map</h3>

                    ${risks.map(risk => `
                        <div class="risk-item">
                            <div class="risk-top">
                                <strong>${escapeHtml(risk.title || "Risk")}</strong>
                                <span>${risk.score ?? 0}/100</span>
                            </div>

                            <div class="risk-bar">
                                <div
                                    class="risk-fill"
                                    style="width:${Math.min(
                                        100,
                                        Math.max(0, Number(risk.score) || 0)
                                    )}%">
                                </div>
                            </div>

                            <p>${escapeHtml(risk.detail || "")}</p>
                        </div>
                    `).join("")}
                </div>

                <div class="report-section">
                    <h3>🥊 Counterarguments</h3>

                    ${counterarguments.map(item => `
                        <div class="bullet-card">
                            ${escapeHtml(item)}
                        </div>
                    `).join("")}
                </div>

                <div class="report-section">
                    <h3>🔀 Alternatives</h3>

                    ${alternatives.map(item => `
                        <div class="bullet-card">
                            ${escapeHtml(item)}
                        </div>
                    `).join("")}
                </div>

                <div class="break-card">
                    <h3>⚡ BREAK MY DECISION</h3>
                    <p>
                        ${escapeHtml(
                            result.break_my_decision ||
                            "No counter-analysis available."
                        )}
                    </p>
                </div>

                <div class="report-section">
                    <h3>🔎 Evidence to Collect</h3>

                    <ul>
                        ${evidence.map(item =>
                            `<li>${escapeHtml(item)}</li>`
                        ).join("")}
                    </ul>
                </div>

                <div class="recommendation">
                    <h3>💡 Recommended Next Step</h3>
                    <p>
                        ${escapeHtml(
                            result.recommendation ||
                            "No recommendation available."
                        )}
                    </p>
                </div>

            </section>
        `;

        resultBox.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });
    }

    function getHighestRisk(risks) {
        if (!risks.length) return "—";

        const highest = risks.reduce((max, item) => {
            return Number(item.score || 0) > Number(max.score || 0)
                ? item
                : max;
        }, risks[0]);

        return `${highest.score || 0}/100`;
    }

    function escapeHtml(value) {
        return String(value)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }
});