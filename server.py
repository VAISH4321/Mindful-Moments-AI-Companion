from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import traceback
import os

# 🔑 Configure Gemini with your API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your api key")
GEMINI_MODEL = "models/gemini-2.5-flash"

genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI()

# Allow frontend calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Journaling endpoint
# ---------------------------
@app.post("/api/journal")
async def journal(req: Request):
    """AI-powered journaling: user entry + AI reflection"""
    data = await req.json()
    entry = (data.get("entry") or "").strip()
    if not entry:
        return {"error": "Journal entry required"}

    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        prompt = (
            "You are a compassionate journaling companion. "
            "When given a user's journal entry, respond with:\n"
            "1. A short empathetic reflection summary.\n"
            "2. A warm encouragement message.\n"
            "3. A follow-up journaling prompt.\n"
            "4. A simple wellbeing tip or exercise.\n"
            "Keep each part concise and supportive.\n\n"
            f"User entry: {entry}"
        )
        response = model.generate_content(prompt)
        lines = response.text.strip().split("\n")
        result = {
            "reflection": lines[0] if len(lines) > 0 else "",
            "encouragement": lines[1] if len(lines) > 1 else "",
            "prompt": lines[2] if len(lines) > 2 else "",
            "tip": lines[3] if len(lines) > 3 else ""
        }
        return {"entry": entry, "ai_response": result}
    except Exception as e:
        traceback.print_exc()
        return {
            "error": "Gemini API error",
            "details": str(e),
            "entry": entry,
            "ai_response": {
                "reflection": "You expressed yourself honestly.",
                "encouragement": "It’s brave to write down your feelings.",
                "prompt": "What helped you cope today?",
                "tip": "Take a short walk to clear your mind."
            }
        }

# ---------------------------
# Chat endpoint
# ---------------------------
@app.post("/api/chat")
async def chat_endpoint(req: Request):
    """Support page: AI chat with mental health focus"""
    data = await req.json()
    user_msg = (data.get("message") or "").strip()
    if not user_msg:
        return {"error": "Message required"}

    # Crisis filter
    crisis_terms = ["suicid", "kill", "die", "end it", "hurt myself", "harm"]
    if any(term in user_msg.lower() for term in crisis_terms):
        return {
            "reply": (
                "I’m really sorry you’re feeling this way. I’m not a mental health professional, "
                "but you deserve immediate care. Please reach out to someone you trust and consider "
                "contacting local emergency services if you may be in danger."
            )
        }

    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        prompt = (
            "You are a compassionate wellness companion. "
            "Always greet the user warmly and respectfully. "
            "Respond only with content related to mental health, emotional wellbeing, self‑care, and supportive lifestyle advice. "
            "Provide encouragement, journaling prompts, mindfulness tips, and practical coping strategies. "
            "Never give medical diagnoses, prescriptions, or clinical treatment plans. "
            "If the user expresses distress or crisis, respond with empathy and encourage them to reach out to trusted people or professional help immediately. "
            "Keep your tone positive, gentle, and supportive. "
            "Avoid technical or unrelated topics; redirect back to wellbeing if asked about other subjects.\n\n"
            f"User: {user_msg}"
        )
        response = model.generate_content(prompt)
        return {"reply": response.text}
    except Exception as e:
        traceback.print_exc()
        return {"error": "Gemini API error", "details": str(e)}

# ---------------------------
# Tips endpoint
# ---------------------------
@app.get("/api/tips")
async def tips():
    """Home page: dynamically generate wellbeing tips, exercises, journaling prompts, affirmations"""
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content([
            {
                "parts": [
                    {
                        "text": (
                            "You are a supportive wellness assistant. "
                            "Respond ONLY with a JSON object with keys: "
                            "\"mindfulness\", \"journaling\", \"exercise\", \"affirmation\". "
                            "Each value should be 1–2 sentences."
                        )
                    },
                    {"text": "Please provide today's wellbeing suggestions."}
                ]
            }
        ])

        # Gemini returns text in response.text
        import json
        # Try parsing as JSON
        tips_json = json.loads(response.text)
        # Ensure all keys exist
        result = {
            "mindfulness": tips_json.get("mindfulness", "Take a deep breath and pause."),
            "journaling": tips_json.get("journaling", "Write one thing you are grateful for."),
            "exercise": tips_json.get("exercise", "Stretch your arms overhead for 10 seconds."),
            "affirmation": tips_json.get("affirmation", "You are strong and capable.")
        }
        return result

    except Exception as e:
        print("Gemini error:", e)
        import traceback; traceback.print_exc()
        # fallback tips
        return {
            "mindfulness": "Take a deep breath and pause.",
            "journaling": "Write one thing you are grateful for.",
            "exercise": "Stretch your arms overhead for 10 seconds.",
            "affirmation": "You are strong and capable."
        }
