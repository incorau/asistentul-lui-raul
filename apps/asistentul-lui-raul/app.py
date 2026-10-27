from flask import Flask, request, jsonify, session, Response
import ollama, json
app = Flask(__name__)
app.secret_key = "incorau-secret"
SYSTEM = "Ești INCORAU AI, asistentul lui Raul. Vorbești doar în română. Răspunzi scurt și prietenos."
def get_istoric():
    if "istoric" not in session:
        session["istoric"] = [{"role":"system","content":SYSTEM}]
    return session["istoric"]
@app.route("/")
def home():
    return """
<!DOCTYPE html><html lang="ro"><head><meta charset="UTF-8"><title>INCORAU AI</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#050510;color:#e2e8f0;font-family:Arial;height:100vh;display:flex}
.sidebar{width:260px;background:#0a0a1e;border-right:1px solid #8b5cf633;padding:20px}
.logo{font-size:28px;font-weight:800;background:linear-gradient(90deg,#8b5cf6,#06b6d4,#22c55e);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.btn{width:100%;padding:12px;border-radius:12px;border:1px solid #ffffff22;background:#ffffff0d;color:white;cursor:pointer;margin-top:12px;font-weight:600}
.main{flex:1;display:flex;flex-direction:column;background:radial-gradient(800px 400px at 50% -100px, rgba(139,92,246,.25), transparent), #050510}
.header{padding:16px 24px;border-bottom:1px solid #ffffff11;display:flex;justify-content:space-between}
.chat{flex:1;overflow-y:auto;padding:24px}
.welcome{max-width:700px;margin:40px auto;text-align:center}
.welcome h1{font-size:44px}
.welcome h1 span{background:linear-gradient(90deg,#a78bfa,#22d3ee);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.welcome p{color:#94a3b8;margin-top:12px}
.msg{max-width:760px;margin:0 auto 16px;display:flex;gap:12px}
.avatar{width:38px;height:38px;border-radius:12px;display:grid;place-items:center;font-weight:700;flex-shrink:0}
.user .avatar{background:linear-gradient(135deg,#2563eb,#06b6d4)}
.ai .avatar{background:linear-gradient(135deg,#7c3aed,#ec4899)}
.bubble{flex:1;line-height:1.6;padding-top:6px}
.bottom{padding:16px 24px}
.box{max-width:760px;margin:0 auto;background:#ffffff10;border:1px solid #ffffff22;border-radius:20px;padding:8px;display:flex;gap:8px}
textarea{flex:1;background:transparent;border:none;color:white;outline:none;resize:none;font-size:16px;padding:10px}
.send{width:44px;height:44px;border:none;border-radius:12px;background:linear-gradient(135deg,#7c3aed,#06b6d4);color:white;cursor:pointer;font-size:18px}
</style></head>
<body>
<div class="sidebar"><div class="logo">INCORAU AI</div><div style="font-size:11px;color:#64748b;letter-spacing:3px">BY RAUL • FUTURE</div><button class="btn" onclick="newChat()">+ Conversație nouă</button></div>
<div class="main"><div class="header"><div>✨ Asistent Personal</div><div>● Online</div></div>
<div id="chat" class="chat"><div class="welcome" id="welcome"><h1>Salut, eu sunt<br><span>INCORAU AI</span></h1><p>Asistentul tău personal, rapid și futuristic.</p></div></div>
<div class="bottom"><div class="box"><textarea id="msg" rows="1" placeholder="Scrie aici..."></textarea><button class="send" onclick="send()">↑</button></div></div></div>
<script>
const chatEl=document.getElementById('chat');
async function newChat(){await fetch("/new_chat",{method:"POST"}); location.reload();}
function add(role,html){ const w=document.getElementById('welcome'); if(w) w.style.display='none'; const d=document.createElement('div'); d.className='msg '+role; d.innerHTML=`<div class="avatar">${role=='user'?'R':'AI'}</div><div class="bubble">${html}</div>`; chatEl.appendChild(d); chatEl.scrollTop=chatEl.scrollHeight; return d.querySelector('.bubble'); }
async function send(){ let m=document.getElementById('msg').value.trim(); if(!m) return; add('user',m); document.getElementById('msg').value=''; let bub=add('ai',''); let full=""; const r=await fetch("/chat_stream",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:m})}); const reader=r.body.getReader(); const dec=new TextDecoder(); while(true){const {done,value}=await reader.read(); if(done) break; let ch=dec.decode(value); for(let line of ch.split("\\n")){ if(line.startsWith("data: ")){ let d=line.slice(6); if(d=="[DONE]") break; try{ let j=JSON.parse(d); full+=j.token; bub.innerText=full+"▌"; }catch(e){} } } } bub.innerText=full; }
document.getElementById('msg').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send();}});
</script></body></html>
"""
@app.route("/new_chat", methods=["POST"])
def new_chat():
    session["istoric"]=[{"role":"system","content":SYSTEM}]
    return jsonify(ok=True)
@app.route("/chat_stream", methods=["POST"])
def chat_stream():
    msg=request.json.get("message","").strip()
    istoric=get_istoric()
    istoric.append({"role":"user","content":msg})
    if len(istoric)>11: istoric=[istoric[0]]+istoric[-10:]
    def gen():
        full=""
        stream=ollama.chat(model="llama3.2:1b", messages=istoric, stream=True, options={"num_ctx":2048})
        for c in stream:
            t=c["message"]["content"]; full+=t
            yield f"data: {json.dumps({'token':t},ensure_ascii=False)}\n\n"
        istoric.append({"role":"assistant","content":full}); session["istoric"]=istoric
        yield "data: [DONE]\n\n"
    return Response(gen(), mimetype="text/event-stream")
if __name__=="__main__":
    app.run(host="127.0.0.1", port=5000, threaded=True)