from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)  # allow Vercel site to call

@app.route("/")
def home():
    return jsonify({
        "status": "TikTok DL API - LIVE",
        "by": "DREAM-MD",
        "test": "/api/tiktok?url=https://www.tiktok.com/@user/video/123",
        "vercel_frontend": "Use this Render URL in your Vercel site"
    })

@app.route("/api/tiktok")
def tiktok_api():
    tiktok_url = request.args.get('url', '').strip()
    if not tiktok_url:
        return jsonify({"error": "Add ?url= tiktok link"}), 400
    if 'tiktok.com' not in tiktok_url:
        return jsonify({"error": "Not a TikTok URL"}), 400

    try:
        # server-side call to tikwm - no CORS
        r = requests.get(
            f"https://tikwm.com/api/?url={tiktok_url}",
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        data = r.json()
        if data.get('code') != 0:
            return jsonify({"error": data.get('msg', 'Failed'), "raw": data}), 500
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/download")
def proxy_download():
    video_url = request.args.get('url', '')
    if not video_url:
        return jsonify({"error": "Missing url"}), 400
    try:
        r = requests.get(video_url, stream=True, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        return Response(
            r.iter_content(chunk_size=8192),
            content_type=r.headers.get('content-type', 'video/mp4'),
            headers={"Content-Disposition": "attachment; filename=tiktok_hd.mp4"}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
