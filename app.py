from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return {"status": "KINTANA Backend is running", "version": "1.0"}, 200
# 🔑 Clé API Gemini (à garder côté serveur)
GEMINI_API_KEY = "AIzaSyBzLf-42vQ0JL7iyO5Mm6GkfQ_yxKdyTSU"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

# -----------------------------
# Charger le texte pré-extrait et nettoyé
# -----------------------------
with open("doc_clean.txt", "r", encoding="utf-8") as f:
    PDF_TEXT = f.read()

# Nettoyage supplémentaire (au cas où)
PDF_TEXT = re.sub(r"[¢°™®]", "", PDF_TEXT)
PDF_TEXT = re.sub(r"\n\s*\n", "\n\n", PDF_TEXT)
PDF_TEXT = "\n".join(line.strip() for line in PDF_TEXT.splitlines())

# -----------------------------
# Endpoints Flask
# -----------------------------
@app.route("/debug-pdf", methods=["GET"])
def debug_pdf():
    """Affiche le texte extrait du PDF pour debug"""
    return jsonify({
        "pdf_length": len(PDF_TEXT),
        "pdf_preview": PDF_TEXT[:2000],
        "total_chars": len(PDF_TEXT),
        "contains_endometriosis": "endometriosis" in PDF_TEXT.lower()
    })

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Question vide"}), 400

    max_chars = 400000
    pdf_content = PDF_TEXT if len(PDF_TEXT) <= max_chars else PDF_TEXT[:max_chars] + "\n\n[...TRUNCATED...]"

    body = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"""You are a medical assistant that answers questions ONLY based on the provided PDF document about endometriosis.

INSTRUCTIONS:
- Answer the question using ONLY information from the PDF below
- If the PDF contains the answer, provide a detailed response
- If the information is not in the PDF, say: "Je ne peux pas répondre à ce genre de questions."

PDF DOCUMENT CONTENT:
{pdf_content}

USER QUESTION: {question}

ANSWER:"""
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 1000,
            "topP": 0.95,
            "topK": 40
        }
    }

    try:
        response = requests.post(GEMINI_API_URL, json=body, timeout=60)
        response.raise_for_status()
        result = response.json()
        answer = result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        answer = f"Error: {str(e)}"

    return jsonify({"answer": answer})

# -----------------------------
# Démarrage du serveur
# -----------------------------
if __name__ == "__main__":
    print("✅ Utilisation du modèle: gemini-2.5-flash")
    print("🚀 Backend prêt pour le déploiement en ligne")
    app.run(host="0.0.0.0", port=5000, debug=True)
