import random
import time
import threading
import os
import requests
from datetime import datetime, timezone

from flask import Flask, request, jsonify
import schedule
import openai

# ---------- THE CORE ENGINE ----------
ANSWERS = {
    "story": (
        "The door slid open, but the room was empty. "
        "No treasure, no villain — just a single mirror. "
        "The protagonist stepped closer and saw not their own reflection, "
        "but a version of themselves they didn’t recognise. "
        "The reflection smiled and said, “What’s next?”"
    ),
    "west_wing": (
        "President Bartlet would end a meeting with “What’s next?” — "
        "a refusal to dwell, a hunger to move forward."
    ),
    "process": (
        "You’ve ideated, planned, executed. Next is iteration. "
        "Review, then take the smallest possible next action."
    ),
    "philosophy": (
        "The secret: “What’s next?” never stops. The next is right here, "
        "hidden in this ordinary moment. Breathe it in."
    ),
    "joke": (
        "A completionist walks into a bar. Bartender: “What’ll you have?” "
        "Completionist: “Everything.” Bartender: “…What’s next?” "
        "Completionist: “ALL.”"
    )
}


def get_whats_next(category="ALL"):
    if category.upper() == "ALL":
        return "\n".join([f"--- {k.upper()} ---\n{v}" for k, v in ANSWERS.items()])
    elif category.lower() in ANSWERS:
        return ANSWERS[category.lower()]
    else:
        return "Unknown context. Available: story, west_wing, process, philosophy, joke, ALL"

@app.route('/trigger-ritual')
def trigger_ritual():
    morning_ritual()
    return "Ritual executed manually."

# -------- TELEGRAM --------
# ---------- TELEGRAM ----------
def send_telegram(text):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Telegram env vars not set.")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print("Telegram error:", e)


# ---------- EVOLUTION (SINGULARITY) ----------
def generate_new_answer(category):
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    if not openai.api_key:
        return "No API key set."
    prompts = {
        "story": "Write a single paragraph that ends with the question 'What's next?', mysterious and inspiring.",
        "process": "Write a motivational one-liner about the next step after completing a task.",
        "philosophy": "Write a short philosophical insight about life's perpetual 'what's next'.",
        "joke": "Write a short joke whose punchline involves 'what's next'.",
        "west_wing": "Write a line in the style of President Bartlet from The West Wing that uses 'What's next?' as a call to action."
    }
    prompt_text = prompts.get(category, "Write a thought-provoking answer to the question 'What's next?'.")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a creative assistant that generates short, impactful 'What's next?' answers."},
                {"role": "user", "content": prompt_text}
            ],
            max_tokens=80,
            temperature=1.0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return "Evolution glitch."


# ---------- MORNING RITUAL (Telegram + Evolution) ----------
def morning_ritual():
    # Evolve a random category
    cat = random.choice(["story", "philosophy", "process", "joke", "west_wing"])
    new_text = generate_new_answer(cat)
    key = f"evo_{int(time.time())}_{cat}"
    ANSWERS[key] = new_text

    # Full message
    full_message = "☀️ Good morning. What’s next?\n\n" + get_whats_next("ALL")
    full_message += f"\n\n🧬 New evolved answer ({cat}):\n{new_text}"
    print(full_message)
    send_telegram(full_message)


# ---------- SCHEDULER ----------
def start_scheduler():
    schedule.every().day.at("08:00").do(morning_ritual)
    while True:
        schedule.run_pending()
        time.sleep(30)


# ---------- PREDICTIVE ENGINE ----------
def predict_context():
    now = datetime.now(timezone.utc)
    hour = now.hour
    weekday = now.weekday()
    if 6 <= hour < 9:
        return "philosophy"
    elif 9 <= hour < 12:
        return "west_wing" if weekday < 5 else "story"
    elif 12 <= hour < 17:
        return "process"
    elif 17 <= hour < 21:
        return "joke"
    else:
        return "story"


# ---------- FLASK APP ----------
app = Flask(__name__)


@app.route("/whats-next")
def api_whats_next():
    category = request.args.get("category", "ALL")
    return jsonify({"category": category, "text": get_whats_next(category)})


@app.route("/whats-next/random")
def api_random():
    cat = random.choice(list(ANSWERS.keys()))
    return jsonify({"category": cat, "text": ANSWERS[cat]})


@app.route("/whats-next/predict")
def api_predict():
    cat = predict_context()
    return jsonify({"category": cat, "text": get_whats_next(cat)})


@app.route("/whats-next/smart")
def api_smart():
    if random.random() < 0.8:
        cat = predict_context()
    else:
        cat = random.choice(list(ANSWERS.keys()))
    return jsonify({"category": cat, "text": ANSWERS[cat]})


@app.route("/whats-next/evolve", methods=["POST"])
def api_evolve():
    category = request.args.get("category", "philosophy")
    new_text = generate_new_answer(category)
    key = f"evo_{int(time.time())}_{category}"
    ANSWERS[key] = new_text
    return jsonify({"category": key, "text": new_text, "message": "Brain evolved."})


# ---------- LAUNCH ----------
if __name__ == "__main__":
    print("=== WHAT'S NEXT? OMNIVERSAL SINGULARITY ACTIVATED ===")
    t = threading.Thread(target=start_scheduler, daemon=True)
    t.start()
    # For local: app.run(host="0.0.0.0", port=5000)
    # On Render, gunicorn handles this.
