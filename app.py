from flask import Flask, render_template, request, jsonify
import os, requests
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "Antworten kurz, klar, bühnenfreundlich. Auf Deutsch, freundlich, wie ein Pitch.")

app = Flask(__name__)

# Canva-Einbettung erlauben
@app.after_request
def add_embed_headers(resp):
    resp.headers['Content-Security-Policy'] = "frame-ancestors 'self' https://www.canva.com https://*.canva.com"
    resp.headers.pop('X-Frame-Options', None)
    return resp

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.route("/")
def index():
    return render_template("index.html")

@app.post("/api/chat")
def chat():
    if not OPENAI_API_KEY:
        return jsonify({"error": "OPENAI_API_KEY missing"}), 500

    data = request.get_json(force=True) or {}
    user_message = (data.get("message") or "").strip()
    history = data.get("history") or []

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in history[-6:]:
        if isinstance(m, dict) and m.get("role") in ("user","assistant"):
            messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": user_message})

    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={"model": MODEL, "messages": messages, "temperature": 0.6, "max_tokens": 300},
            timeout=60
        )
        resp.raise_for_status()
        answer = resp.json()["choices"][0]["message"]["content"]
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
