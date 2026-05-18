from flask import Flask, render_template, request, jsonify
import requests as req_lib
from yaml_to_html_table import yaml_to_html_table

app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/render")
def render():
    data = request.get_json(force=True) or {}
    url = (data.get("url") or "").strip()
    yaml_text = (data.get("yaml_text") or "").strip()
    color = (data.get("color") or "").strip() or None

    if url:
        try:
            resp = req_lib.get(url, timeout=10)
            resp.raise_for_status()
            yaml_text = resp.text
        except req_lib.exceptions.Timeout:
            return jsonify({"error": f"Request timed out fetching: {url}"})
        except req_lib.exceptions.RequestException as e:
            return jsonify({"error": f"Failed to fetch URL: {e}"})

    if not yaml_text:
        return jsonify({"error": "Provide a URL or paste YAML text."})

    try:
        html = yaml_to_html_table(yaml_text, gradient_hex=color)
        return jsonify({"html": html})
    except Exception as e:
        return jsonify({"error": f"Failed to parse YAML: {e}"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
