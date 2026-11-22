import base64
import os

from anthropic import Anthropic
from flask import Flask, jsonify, request

app = Flask(__name__)
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

PROMPT = (
    "Tu es un analyste tactique de football. Analyse cette image de match "
    "et réponds en français, de façon claire et courte : "
    "1) la phase de jeu, 2) le schéma tactique probable, "
    "3) le placement des joueurs, 4) les espaces libres, "
    "5) les points forts et les faiblesses. "
    "Si une information n'est pas visible, dis-le."
)

PAGE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Analyse de match</title>
<style>
body { font-family: sans-serif; margin: 0; padding: 16px; }
img { max-width: 100%; margin-top: 12px; border-radius: 8px; }
button { padding: 12px 18px; font-size: 16px; margin-top: 12px; }
#resultat { white-space: pre-wrap; margin-top: 16px; line-height: 1.5; }
</style>
</head>
<body>
<h2>Analyse d'image de match</h2>
<input type="file" id="fichier" accept="image/*"><br>
<button id="bouton">Analyser</button>
<img id="apercu" alt="">
<div id="resultat"></div>
<script>
const fichier = document.getElementById("fichier");
const apercu = document.getElementById("apercu");
const resultat = document.getElementById("resultat");
fichier.addEventListener("change", () => {
  const f = fichier.files[0];
  if (f) apercu.src = URL.createObjectURL(f);
});
document.getElementById("bouton").addEventListener("click", async () => {
  const f = fichier.files[0];
  if (!f) { resultat.textContent = "Choisis d'abord une image."; return; }
  resultat.textContent = "Analyse en cours...";
  const form = new FormData();
  form.append("image", f);
  try {
    const r = await fetch("/analyser", { method: "POST", body: form });
    const json = await r.json();
    resultat.textContent = json.analyse || json.erreur;
  } catch (e) {
    resultat.textContent = "Erreur, réessaie.";
  }
});
</script>
</body>
</html>"""


@app.route("/")
def index():
    return PAGE


@app.route("/analyser", methods=["POST"])
def analyser():
    fichier = request.files.get("image")
    if fichier is None:
        return jsonify({"erreur": "Aucune image reçue."}), 400

    donnees = base64.standard_b64encode(fichier.read()).decode("utf-8")
    type_media = fichier.mimetype or "image/jpeg"

    reponse = client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=1200,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": type_media,
                            "data": donnees,
                        },
                    },
                    {"type": "text", "text": PROMPT},
                ],
            }
        ],
    )
    return jsonify({"analyse": reponse.content[0].text})
