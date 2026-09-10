from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests, os, re
import yt_dlp

app = Flask(__name__)
CORS(app)

def get_info(url, extra_opts={}):
    opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        **extra_opts
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)

@app.route("/")
def home():
    return jsonify({
        "status": "FAVOUR DL PRO - ALL IN ONE",
        "platforms": ["tiktok","youtube","instagram","facebook","twitter","x.com","twitch","reddit","vimeo"],
        "features": ["hd_no_watermark","mp3","thumbnail_hd","subtitles","multiple_qualities","proxy_download","audio_extract","profile_pic"],
        "endpoints": {
            "/api/all?url=": "Auto detect",
            "/api/tiktok?url=": "TikTok HD no WM + MP3 + HD thumb",
            "/api/youtube?url=": "YouTube 4K/1080/720 + MP3 + subs + thumb",
            "/api/instagram?url=": "IG Reels/Posts/Stories",
            "/api/facebook?url=": "FB videos",
            "/api/twitter?url=": "Twitter/X videos",
            "/api/thumbnail?url=": "HD thumbnail only",
            "/api/mp3?url=": "Direct MP3 audio"
        }
    })

@app.route("/api/tiktok")
def tiktok():
    url=request.args.get('url','').strip()
    if not url: return jsonify({"error":"Missing url"}),400
    try:
        r=requests.get(f"https://tikwm.com/api/?url={url}",timeout=20,headers={"User-Agent":"Mozilla/5.0"})
        j=r.json()
        if j.get('code')!=0:
            # fallback to yt-dlp
            info=get_info(url)
            return jsonify({"platform":"tiktok","fallback":True,"title":info.get('title'),"thumbnail":info.get('thumbnail'),"best_url":info.get('url'),"formats":info.get('formats',[])[:10]})
        data=j['data']
        return jsonify({
            "platform":"tiktok",
            "title":data.get('title'),
            "author":data.get('author'),
            "duration":data.get('duration'),
            "cover":data.get('cover'),
            "origin_cover":data.get('origin_cover'),
            "hdplay":data.get('hdplay'),
            "play":data.get('play'),
            "wmplay":data.get('wmplay'),
            "music":data.get('music'),
            "music_info":data.get('music_info'),
            "images":data.get('images'), # for photo carousel
            "raw":data
        })
    except Exception as e:
        return jsonify({"error":str(e)}),500

def yt_dlp_response(url):
    try:
        info=get_info(url)
        fmts=[]
        for f in (info.get('formats') or [])[-20:]:
            fmts.append({
                "format_id":f.get('format_id'),
                "ext":f.get('ext'),
                "resolution":f.get('resolution') or f"{f.get('width','')}x{f.get('height','')}",
                "height":f.get('height'),
                "fps":f.get('fps'),
                "filesize":f.get('filesize') or f.get('filesize_approx'),
                "vcodec":f.get('vcodec'),
                "acodec":f.get('acodec'),
                "url":f.get('url')
            })
        fmts=sorted(fmts,key=lambda x:(x.get('height') or 0),reverse=True)
        # best mp4
        mp4s=[f for f in fmts if f['ext']=='mp4' and f['vcodec']!='none']
        best=info.get('url') or (mp4s[0]['url'] if mp4s else (fmts[0]['url'] if fmts else None))
        return jsonify({
            "platform":"yt-dlp",
            "title":info.get('title'),
            "uploader":info.get('uploader'),
            "duration":info.get('duration'),
            "thumbnail":info.get('thumbnail'),
            "thumbnails":info.get('thumbnails',[])[-3:],
            "description":(info.get('description') or '')[:300],
            "webpage_url":info.get('webpage_url'),
            "best_url":best,
            "formats":fmts,
            "subtitles":list((info.get('subtitles') or {}).keys())[:10],
            "automatic_captions":list((info.get('automatic_captions') or {}).keys())[:10]
        })
    except Exception as e:
        return jsonify({"error":str(e)}),500

@app.route("/api/youtube")
def youtube(): return yt_dlp_response(request.args.get('url',''))
@app.route("/api/instagram")
def ig(): return yt_dlp_response(request.args.get('url',''))
@app.route("/api/facebook")
def fb(): return yt_dlp_response(request.args.get('url',''))
@app.route("/api/twitter")
def tw(): return yt_dlp_response(request.args.get('url',''))
@app.route("/api/all")
def all_dl():
    url=request.args.get('url','').strip()
    if not url: return jsonify({"error":"Missing url"}),400
    if 'tiktok.com' in url:
        # try tikwm first
        try:
            r=requests.get(f"https://tikwm.com/api/?url={url}",timeout=15,headers={"User-Agent":"Mozilla/5.0"})
            j=r.json()
            if j.get('code')==0:
                return jsonify({"platform":"tiktok","data":j['data']})
        except: pass
    return yt_dlp_response(url)

@app.route("/api/thumbnail")
def thumb():
    url=request.args.get('url','')
    if not url: return jsonify({"error":"Missing url"}),400
    try:
        info=get_info(url)
        return jsonify({"thumbnails":info.get('thumbnails'),"thumbnail":info.get('thumbnail'),"title":info.get('title')})
    except Exception as e:
        return jsonify({"error":str(e)}),500

@app.route("/api/mp3")
def mp3():
    url=request.args.get('url','')
    if not url: return jsonify({"error":"Missing url"}),400
    try:
        opts={'format':'bestaudio/best','quiet':True,'noplaylist':True}
        info=get_info(url,opts)
        # find best audio
        fmts=info.get('formats',[])
        audios=[f for f in fmts if f.get('vcodec')=='none' and f.get('acodec')!='none']
        best=audios[-1] if audios else (fmts[-1] if fmts else None)
        return jsonify({"title":info.get('title'),"audio_url":best.get('url') if best else info.get('url'),"duration":info.get('duration')})
    except Exception as e:
        return jsonify({"error":str(e)}),500

@app.route("/api/proxy")
def proxy():
    u=request.args.get('url','')
    if not u: return jsonify({"error":"Missing url"}),400
    try:
        r=requests.get(u,stream=True,timeout=30,headers={"User-Agent":"Mozilla/5.0"})
        return Response(r.iter_content(8192),content_type=r.headers.get('content-type','video/mp4'),headers={"Content-Disposition":"attachment; filename=favour_dl_hd.mp4"})
    except Exception as e:
        return jsonify({"error":str(e)}),500

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
