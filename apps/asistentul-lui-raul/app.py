from flask import Flask, request, jsonify, session, Response
import ollama, json
app = Flask(__name__)
app.secret_key = "raul-secret"
SYSTEM = "Ești Asistentul lui Raul. Vorbești doar în română. Răspunzi scurt și prietenos."
def get_istoric():
    if "istoric" not in session:
        session["istoric"] = [{"role":"system","content":SYSTEM}]
    return session["istoric"]
@app.route("/")
def home():
    return """<!DOCTYPE html><html lang="ro"><head><meta charset="UTF-8"><title>Raul</title>
<style>body{background:#0f172a;color:white;font-family:Arial;height:100vh;display:flex;flex-direction:column} .header{background:#1e293b;padding:20px;text-align:center;font-size:26px} .chat{flex:1;overflow-y:auto;padding:20px} .user{background:#2563eb;padding:12px;border-radius:12px;margin:8px 0;margin-left:auto;max-width:80%;width:fit-content} .ai{background:#1e293b;padding:12px;border-radius:12px;margin:8px 0;max-width:80%} .bottom{display:flex;gap:10px;padding:15px;background:#1e293b} textarea{flex:1;height:60px;border-radius:10px;padding:10px} button{background:#22c55e;color:white;border:none;padding:12px 20px;border-radius:10px;cursor:pointer}</style></head>
<body><div class="header">🤖 Raul RAPID</div><div id="chat" class="chat"></div>
<div class="bottom"><textarea id="msg" placeholder="Scrie..."></textarea><button onclick="trimite()">Trimite</button></div>
<script>
async function trimite(){
 let m=document.getElementById("msg").value.trim(); if(!m) return;
 let c=document.getElementById("chat");
 c.innerHTML+=`<div class="user">${m}</div>`; document.getElementById("msg").value="";
 c.innerHTML+=`<div class="ai" id="cur"></div>`; let full="";
 const r=await fetch("/chat_stream",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:m})});
 const reader=r.body.getReader(); const dec=new TextDecoder();
 while(true){const {done,value}=await reader.read(); if(done) break; let chunk=dec.decode(value);
  for(let line of chunk.split("\\n")){ if(line.startsWith("data: ")){ let d=line.slice(6); if(d=="[DONE]") break; try{ let j=JSON.parse(d); full+=j.token; document.getElementById("cur").innerText=full; }catch(e){} } } }
 document.getElementById("cur").removeAttribute("id");
}
document.getElementById("msg").addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();trimite();}});
</script></body></html>"""
@app.route("/chat_stream", methods=["POST"])
def chat_stream():
    msg=request.json.get("message","")
    istoric=get_istoric()
    istoric.append({"role":"user","content":msg})
    if len(istoric)>11: istoric=[istoric[0]]+istoric[-10:]
    def gen():
        full=""
        stream=ollama.chat(model="llama3.2:1b", messages=istoric, stream=True, options={"num_ctx":2048})
        for ch in stream:
            t=ch["message"]["content"]; full+=t
            yield f"data: {json.dumps({'token':t},ensure_ascii=False)}\n\n"
        istoric.append({"role":"assistant","content":full}); session["istoric"]=istoric
        yield "data: [DONE]\n\n"
    return Response(gen(), mimetype="text/event-stream")
if __name__=="__main__":
    app.run(host="127.0.0.1", port=5000, threaded=True)