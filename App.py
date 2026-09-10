from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app, origins="*")  # Allow Vercel frontend to call

@app.route("/")
def home():
    return jsonify({
        "status": "DREAM-MD TikTok API running",
        "endpoints": {
            "/api/tiktok?url=<tiktok_url>": "Get HD video info (no watermark)",
            "/api/download?url=<video_url>": "Proxy download to force save"
        },
        "usage": "Deploy this on Render, put URL in Vercel frontend"
    })

@app.route("/api/tiktok")
def tiktok_api():
    url = request.args.get('url', '').strip()
    if not url:
        return jsonify({"error": "Missing ?url parameter. Example: /api/tiktok?url=https://vm.tiktok.com/XYZ"}), 400
    
    if 'tiktok.com' not in url and 'vm.tiktok' not in url and 'vt.tiktok' not in url:
        return jsonify({"error": "Invalid TikTok URL"}), 400

    try:
        # Call tikwm API from server side - no CORS issue
        api_url = f"https://tikwm.com/api/?url={url}"
        r = requests.get(api_url, timeout=20, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        data = r.json()
        
        if data.get('code') != 0:
            return jsonify({"error": data.get('msg', 'Failed to fetch video'), "raw": data}), 500
        
        # Normalize response for frontend
        # tikwm returns: {code:0, data:{play, hdplay, music, cover, author, title...}}
        return jsonify(data)
    
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/download")
def download_proxy():
    """Proxy to force download - helps bypass CORS and force save dialog"""
    video_url = request.args.get('url', '').strip()
    if not video_url:
        return jsonify({"error": "Missing ?url"}), 400
    
    try:
        r = requests.get(video_url, stream=True, timeout=30, headers={
            "User-Agent": "Mozilla/5.0"
        })
        # Stream back to user as attachment
        return Response(
            r.iter_content(chunk_size=8192),
            content_type=r.headers.get('content-type', 'video/mp4'),
            headers={
                "Content-Disposition": "attachment; filename=tiktok_hd_no_watermark.mp4",
                "Access-Control-Allow-Origin": "*"
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
