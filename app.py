import os
import json
import re
import sqlite3
from datetime import datetime

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(override=True)

app = Flask(__name__)

DB = "data/decisions.db"


# ============================================================
# DATABASE
# ============================================================

def init_db():
    os.makedirs("data", exist_ok=True)

    with sqlite3.connect(DB) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision TEXT NOT NULL,
                goal TEXT,
                constraints TEXT,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


# ============================================================
# FALLBACK ANALYSIS
# Used only if Gemini is unavailable
# ============================================================

def fallback_analysis(decision, goal="", constraints=""):

    text = decision.lower()

    # --------------------------------------------------------
    # Detect a basic decision category
    # --------------------------------------------------------

    if any(word in text for word in [
        "job", "career", "offer", "company", "work",
        "salary", "employment"
    ]):
        decision_type = "Career"

        factors = [
            "Compensation",
            "Role and responsibilities",
            "Learning and skill growth",
            "Career progression",
            "Location and work conditions"
        ]

    elif any(word in text for word in [
        "business", "startup", "shop", "restaurant",
        "customer", "product", "sell"
    ]):
        decision_type = "Business"

        factors = [
            "Customer demand",
            "Pricing",
            "Competition",
            "Operating cost",
            "Ability to execute"
        ]

    elif any(word in text for word in [
        "buy", "purchase", "laptop", "phone",
        "computer", "car", "device"
    ]):
        decision_type = "Purchase"

        factors = [
            "Actual need",
            "Budget",
            "Alternatives",
            "Expected usage",
            "Long-term value"
        ]

    elif any(word in text for word in [
        "course", "degree", "college", "study",
        "exam", "certification", "education"
    ]):
        decision_type = "Education"

        factors = [
            "Career relevance",
            "Learning value",
            "Time commitment",
            "Cost",
            "Alternative learning paths"
        ]

    elif any(word in text for word in [
        "project", "application", "software",
        "website", "app", "technology", "tech"
    ]):
        decision_type = "Technology / Project"

        factors = [
            "Technical feasibility",
            "Required skills",
            "Time to build",
            "User value",
            "Scalability"
        ]

    else:
        decision_type = "General Decision"

        factors = [
            "Expected benefit",
            "Cost or downside",
            "Uncertainty",
            "Alternatives",
            "Reversibility"
        ]

    # --------------------------------------------------------
    # Generic fallback structure
    # --------------------------------------------------------

    return {
        "decision_type": decision_type,

        "key_factors": factors,

        "summary": (
            f"This is primarily a {decision_type.lower()} decision. "
            f"The main question is whether the expected benefit justifies "
            f"the cost, uncertainty, and opportunity cost."
        ),

        "assumptions": [
            {
                "title": "Expected outcome",
                "statement": (
                    "The expected benefit will actually occur at the "
                    "level assumed by the decision-maker."
                ),
                "test": (
                    "Define a measurable outcome and find evidence "
                    "from similar real-world situations."
                )
            },
            {
                "title": "Available resources",
                "statement": (
                    "The available time, money, skills, and support "
                    "are sufficient."
                ),
                "test": (
                    "Create a realistic resource estimate and compare "
                    "it with what is actually available."
                )
            },
            {
                "title": "Alternative quality",
                "statement": (
                    "The alternatives being considered are genuinely "
                    "less attractive."
                ),
                "test": (
                    "Compare at least two realistic alternatives using "
                    "the same criteria."
                )
            }
        ],

        "most_dangerous_assumption": (
            "The expected outcome will be significantly better than "
            "the realistic alternatives."
        ),

        "blind_spots": [
            "The downside of making the wrong decision has not been fully quantified.",
            "The decision may be based on expectations rather than verified evidence.",
            "The possibility of choosing a smaller or reversible option has not been sufficiently explored."
        ],

        "risks": [
            {
                "title": "Uncertainty risk",
                "detail": "Important information is still unknown.",
                "score": 75
            },
            {
                "title": "Opportunity cost",
                "detail": "Choosing this option may prevent a better alternative.",
                "score": 65
            },
            {
                "title": "Execution risk",
                "detail": "The expected result may be harder to achieve than planned.",
                "score": 60
            }
        ],

        "counterarguments": [
            "The decision may be attractive because the expected benefit is easier to imagine than the downside.",
            "A smaller experiment could produce useful evidence before making a full commitment.",
            "The best option may depend on information that has not yet been collected."
        ],

        "alternatives": [
            "Run a smaller or reversible version of the decision first.",
            "Compare the current option with two realistic alternatives.",
            "Set a measurable success threshold before committing fully."
        ],

        "break_my_decision": (
            "Assume this decision is wrong. The strongest argument against "
            "it is that the expected outcome may be overestimated while the "
            "downside and opportunity cost are underestimated. Identify the "
            "single assumption that would cause the entire plan to fail "
            "and test that assumption first."
        ),

        "evidence_to_collect": [
            "Real-world feedback from people affected by the decision",
            "Cost and resource estimates",
            "Evidence from comparable situations",
            "At least two realistic alternatives",
            "A measurable success criterion"
        ],

        "decision_rule": (
            "Proceed only if the highest-risk assumption can be supported "
            "with evidence and the downside remains acceptable."
        ),

        "recommendation": (
            "Do not commit fully until the highest-risk assumption has "
            "been tested with a small, measurable experiment."
        ),

        "confidence": 65
    }


# ============================================================
# GEMINI ANALYSIS
# ============================================================

def ai_analysis(decision, goal, constraints):

    load_dotenv(override=True)

    key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL") or "gemini-3.6-flash"

    print("\n========================================")
    print("DECISION BREAKER AI")
    print("========================================")
    print("GEMINI KEY FOUND:", bool(key))
    print("GEMINI MODEL:", model)

    if not key:

        print("GEMINI ERROR: API key not found")
        print("========================================\n")

        return (
            fallback_analysis(
                decision,
                goal,
                constraints
            ),
            "demo"
        )

    try:

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=key)

        # ----------------------------------------------------
        # IMPORTANT:
        # The prompt forces Gemini to understand the decision
        # BEFORE generating the analysis.
        # ----------------------------------------------------

        prompt = f"""
You are Decision Breaker AI.

You are NOT a generic chatbot.

Your purpose is to STRESS-TEST decisions.

The user gives you a decision. Your job is to understand the
specific situation first, identify what kind of decision it is,
find the assumptions that actually matter for THAT decision,
and then challenge it.

============================================================
USER INPUT
============================================================

Decision:
{decision}

Main goal:
{goal}

Constraints / resources:
{constraints}

============================================================
STEP 1 — CLASSIFY THE DECISION
============================================================

Determine the most appropriate decision type.

Choose one:

Career
Business
Education
Purchase
Finance
Technology
Project
Personal
Relationship
Health
Other

Do not force the decision into an unrelated category.

============================================================
STEP 2 — UNDERSTAND THE DECISION
============================================================

Identify the specific factors that actually matter.

Examples:

Career:
salary, role, technology, learning, growth, location,
stability, opportunity cost

Business:
customer demand, pricing, competition, margins,
operating costs, acquisition, execution

Purchase:
actual need, budget, specifications, usage,
alternatives, lifespan, timing

Education:
career relevance, learning value, cost,
time, prerequisites, alternative paths

Technology/project:
technical feasibility, users, complexity,
skills, time, maintenance, scalability

These are examples only.

Do NOT copy these lists automatically.

Choose factors based on the user's actual decision.

============================================================
STEP 3 — FIND REAL ASSUMPTIONS
============================================================

Do NOT use generic assumptions such as:

"People will like it."

"Resources may be insufficient."

"Competition may exist."

unless they are genuinely relevant.

Every assumption must be connected to something
specific in the user's decision.

For each assumption provide:

title
statement
test

============================================================
STEP 4 — FIND THE MOST DANGEROUS ASSUMPTION
============================================================

Identify ONE assumption that is most likely to break
the entire decision if it turns out to be false.

Explain why it matters.

============================================================
STEP 5 — FIND BLIND SPOTS
============================================================

Find things the user probably has NOT considered.

Avoid repeating the assumptions.

Blind spots should be specific to the decision.

============================================================
STEP 6 — RISK MAP
============================================================

Create 3–5 meaningful risks.

Each risk must have:

title
detail
score

score must be an integer from 0 to 100.

Higher score = greater potential impact or likelihood.

Avoid generic risks unless they truly apply.

============================================================
STEP 7 — COUNTERARGUMENTS
============================================================

Actively argue AGAINST the user's decision.

Do not simply repeat the risks.

Imagine that a smart person strongly disagrees with
the user's plan.

Give 3 strong counterarguments.

============================================================
STEP 8 — ALTERNATIVES
============================================================

Generate 3 realistic alternatives.

Alternatives must be different strategies, not generic advice.

For example:

Instead of:
"Do more research."

Prefer:
"Accept the current job while continuing a targeted
job search for 30 days."

============================================================
STEP 9 — BREAK MY DECISION
============================================================

Assume the user's decision is WRONG.

Construct the strongest case against it.

Answer:

"What would have to be true for this decision to fail?"

Be specific.

============================================================
STEP 10 — EVIDENCE PLAN
============================================================

Tell the user exactly what evidence they should collect
BEFORE committing.

Avoid vague statements such as:

"Do more research."

Give concrete evidence.

============================================================
STEP 11 — DECISION RULE
============================================================

Create a practical rule for deciding.

Example:

"Choose option A if X is true and Y is acceptable.
Choose option B if X cannot be verified."

The rule must relate to the actual decision.

============================================================
STEP 12 — RECOMMENDATION
============================================================

Give a balanced recommendation.

Do NOT automatically say:

"Don't commit yet."

Only recommend waiting, testing, proceeding,
or choosing an alternative based on the actual analysis.

============================================================
IMPORTANT BEHAVIOR
============================================================

DO NOT produce the same structure of assumptions for
every decision.

DO NOT automatically mention:

competition
resources
execution
demand

unless relevant.

DO NOT blindly agree with the user.

DO NOT invent facts.

If important information is missing, acknowledge it.

The analysis must feel like it was written specifically
for THIS decision.

============================================================
RETURN FORMAT
============================================================

Return ONLY valid JSON.

Use exactly these fields:

{{
    "decision_type": "string",

    "key_factors": [
        "string"
    ],

    "summary": "string",

    "assumptions": [
        {{
            "title": "string",
            "statement": "string",
            "test": "string"
        }}
    ],

    "most_dangerous_assumption": "string",

    "blind_spots": [
        "string"
    ],

    "risks": [
        {{
            "title": "string",
            "detail": "string",
            "score": 0
        }}
    ],

    "counterarguments": [
        "string"
    ],

    "alternatives": [
        "string"
    ],

    "break_my_decision": "string",

    "evidence_to_collect": [
        "string"
    ],

    "decision_rule": "string",

    "recommendation": "string",

    "confidence": 0
}}

Rules:

- confidence must be an integer from 0 to 100.
- risk score must be an integer from 0 to 100.
- assumptions must contain title, statement and test.
- Do not output Markdown.
- Do not output ```json.
- Output JSON only.
"""

        # ----------------------------------------------------
        # GEMINI REQUEST
        # ----------------------------------------------------

        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        print("GEMINI RESPONSE RECEIVED")

        raw = response.text.strip()

        # ----------------------------------------------------
        # CLEAN JSON
        # ----------------------------------------------------

        if raw.startswith("```"):

            raw = re.sub(
                r"^```(?:json)?\s*",
                "",
                raw
            )

            raw = re.sub(
                r"\s*```$",
                "",
                raw
            )

        result = json.loads(raw)

        # ----------------------------------------------------
        # BASIC VALIDATION
        # ----------------------------------------------------

        required_fields = [
            "decision_type",
            "key_factors",
            "summary",
            "assumptions",
            "most_dangerous_assumption",
            "blind_spots",
            "risks",
            "counterarguments",
            "alternatives",
            "break_my_decision",
            "evidence_to_collect",
            "decision_rule",
            "recommendation",
            "confidence"
        ]

        missing = [
            field
            for field in required_fields
            if field not in result
        ]

        if missing:

            raise ValueError(
                f"Gemini response missing fields: {missing}"
            )

        print("GEMINI JSON PARSED SUCCESSFULLY")
        print("AI ANALYSIS SUCCESSFUL")
        print("========================================\n")

        return result, "ai"

    except Exception as e:

        print("========================================")
        print("GEMINI AI ERROR:")
        print(repr(e))
        print("========================================\n")

        return (
            fallback_analysis(
                decision,
                goal,
                constraints
            ),
            "demo"
        )


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def index():

    return render_template("index.html")


# ============================================================
# ANALYZE DECISION
# ============================================================

@app.post("/analyze")
def analyze():

    decision = request.form.get(
        "decision",
        ""
    ).strip()

    goal = request.form.get(
        "goal",
        ""
    ).strip()

    constraints = request.form.get(
        "constraints",
        ""
    ).strip()

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    if len(decision) < 10:

        return jsonify({
            "error": (
                "Please describe the decision "
                "in at least 10 characters."
            )
        }), 400

    # --------------------------------------------------------
    # AI analysis
    # --------------------------------------------------------

    result, mode = ai_analysis(
        decision,
        goal,
        constraints
    )

    # --------------------------------------------------------
    # Save analysis
    # --------------------------------------------------------

    with sqlite3.connect(DB) as con:

        con.execute(
            """
            INSERT INTO analyses
            (
                decision,
                goal,
                constraints,
                result_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                decision,
                goal,
                constraints,
                json.dumps(result),
                datetime.utcnow().isoformat()
            )
        )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return jsonify({
        "result": result,
        "mode": mode
    })


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return jsonify({
        "status": "ok"
    })


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

init_db()


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
