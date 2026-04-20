"""
app.py — Flask backend for Gene → Drug Pipeline web app
Exposes one main endpoint: POST /api/pipeline
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import logging
import os

from src.pipeline import run_pipeline

app = Flask(__name__)
CORS(app)  # Allow frontend JS to call the API

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ── Serve the frontend ──────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


# ── Main pipeline endpoint ───────────────────────────────────────
@app.route("/api/pipeline", methods=["POST"])
def pipeline():
    """
    POST /api/pipeline
    Body: { "gene": "TP53" }
    Returns: full pipeline JSON result
    """
    body = request.get_json(silent=True)
    if not body or not body.get("gene"):
        return jsonify({"error": "Missing 'gene' in request body"}), 400

    gene = body["gene"].strip()
    if not gene.isalnum() or len(gene) > 20:
        return jsonify({"error": "Invalid gene name. Use standard HGNC symbols (e.g. TP53, BRCA1)"}), 400

    try:
        logger.info(f"Pipeline request: {gene}")
        result = run_pipeline(gene_name=gene, use_cache=True)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Pipeline error for {gene}: {e}")
        return jsonify({"error": str(e), "gene": gene}), 500


# ── Health check (for Render / uptime monitors) ─────────────────
@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
