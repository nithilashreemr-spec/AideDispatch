import tkinter as tk
from tkinter import font as tkfont
import threading, queue, csv, os, re, math, heapq, time
import webbrowser, json, difflib, urllib.request
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False



#  PHONETIC / NLP CORRECTION  (v2)


PHONETIC_MAP = {
    "chest pain":"chest pain","chest pains":"chest pain","chest is paining":"chest pain",
    "chest is hurting":"chest pain","chest tightness":"chest tightness","chest is tight":"chest tightness",
    "chest pressure":"chest pain","pressure in chest":"chest pain","heaviness in chest":"chest pain",
    "heavy chest":"chest pain","pain in chest":"chest pain","lest pain":"chest pain",
    "lest pains":"chest pain","jest pain":"chest pain","best pain":"chest pain",
    "test pain":"chest pain","chest payne":"chest pain","just pain":"chest pain",
    "yes pain":"chest pain","chest plane":"chest pain","chest paying":"chest pain","chest ache":"chest pain",
    "not breathing":"not breathing","stopped breathing":"stopped breathing",
    "not reading":"not breathing","not breeding":"not breathing",
    "stopped reading":"stopped breathing","stopped breeding":"stopped breathing",
    "can't breathe":"can't breathe","cant breathe":"can't breathe","cannot breathe":"can't breathe",
    "can't read":"can't breathe","cant read":"can't breathe","can't breed":"can't breathe",
    "no air":"can't breathe","short of breath":"short of breath","short of breathe":"short of breath",
    "shortage breath":"short of breath","shortness of breath":"short of breath","short breath":"short of breath",
    "breathing":"breathing","breed in":"breathing","breeding":"breathing","breading":"breathing","bred in":"breathing",
    "cardiac arrest":"cardiac arrest","cardiac rest":"cardiac arrest",
    "heart attack":"heart attack","hard attack":"heart attack","heart act":"heart attack",
    "hot attack":"heart attack","heart attic":"heart attack","heart tack":"heart attack",
    "heart stopped":"heart stopped","heart stop":"heart stopped",
    "no heartbeat":"no heartbeat","no heart beat":"no heartbeat",
    "no pulse":"no pulse","no pulsed":"no pulse","low pulse":"low pulse","weak pulse":"weak pulse",
    "faint pulse":"faint pulse","pulse is low":"low pulse","pulse is weak":"weak pulse",
    "pulse low":"low pulse","pulse weak":"weak pulse","heart racing":"heart racing",
    "palpitation":"palpitation","palpitations":"palpitation","cardiac":"cardiac",
    "car deck":"cardiac","car jack":"cardiac","pulsed":"pulse","polls":"pulse",
    "unconscious":"unconscious","unconfirmed":"unconscious","uncle shes":"unconscious",
    "not conscious":"unconscious","un conscious":"unconscious","becomes unconscious":"unconscious",
    "became unconscious":"unconscious","going unconscious":"unconscious",
    "unresponsive":"unresponsive","non responsive":"unresponsive","not responsive":"unresponsive",
    "not responding":"not responding","won't wake":"won't wake","wont wake":"won't wake",
    "not waking":"won't wake","passed out":"passed out","past out":"passed out",
    "path out":"passed out","collapsed":"collapsed","collapsing":"collapsing",
    "conscious":"conscious","is conscious":"conscious","still conscious":"conscious","becoming conscious":"conscious",
    "sees her":"seizure","sees him":"seizure","sees you":"seizure","season":"seizure","seize her":"seizure",
    "seizing":"seizing","convulsing":"convulsing","consulting":"convulsing","convulsion":"convulsing","fitting":"fitting",
    "joking":"choking","smoking":"choking","chopping":"choking","chocking":"choking","checking":"choking",
    "painting":"fainting","feinting":"fainting","fainting":"fainting","fainted":"fainted","paint":"faint",
    "drowning":"drowning","browning":"drowning","crowning":"drowning","frowning":"drowning","droning":"drowning",
    "fell in water":"fell in water","fallen in water":"fell in water",
    "underwater":"underwater","under water":"underwater","submerged":"submerged",
    "heavy bleeding":"heavy bleeding","bleeding badly":"bleeding badly","blood everywhere":"blood everywhere",
    "losing blood":"losing blood","loosing blood":"losing blood","lot of blood":"lot of blood",
    "bleeding":"bleeding","pleading":"bleeding","bleed in":"bleeding",
    "rapped":"trapped","wrapped":"trapped","crapped":"trapped",
    "can't get out":"trapped","cannot get out":"trapped",
    "result":"assault","a salt":"assault","stabbing":"stabbing","stabbed":"stabbed",
    "building on fire":"building on fire","house on fire":"house on fire",
    "gas leak":"gas leak","gas lick":"gas leak","burning":"burning","bursting":"burning","fighting":"fire",
    "collusion":"collision","hit by car":"hit by car","knocked down":"knocked down",
    "ran over":"ran over","run over":"ran over",
    "behosh":"unconscious","hosh mein nahi":"unconscious","gir gaya":"collapsed","gir gayi":"collapsed",
    "saas nahi aa rahi":"not breathing","saas nahi":"not breathing","dhadkan band":"heart stopped",
    "dhadkan nahi":"no heartbeat","seene mein dard":"chest pain","sine mein dard":"chest pain",
    "khoon aa raha":"bleeding","khoon":"bleeding","bahut dard":"severe pain","dard":"pain",
    "chot":"injury","aag lagi":"fire","aag":"fire","pani mein":"in water","dub raha":"drowning",
    "sar mein chot":"head injury","girna":"fell",
    "chor":"thief","chori":"theft","chori ho gayi":"theft occurred",
    "dakaiti":"robbery","dakait":"robber","loot":"robbery","lootna":"robbery",
    "ghar mein ghusa":"broke in","mobile churaya":"phone stolen",
    "wallet chori":"wallet stolen","purse chori":"purse stolen",
    "gaadi chori":"vehicle stolen","bike chori":"bike stolen",
    "snatch":"snatching","chain snatch":"chain snatching","mug":"mugging",
    "pick pocket":"pickpocket","break in":"broke in","burglar":"burglar",
    "shoplifter":"shoplifting","vandal":"vandalism","trespass":"trespassing",
}

NLP_VOCAB = [
    "conscious","fainting","fainted","faint","seizure","seizing","fitting",
    "choking","choked","drowning","drowned","breathing","breathe","breath",
    "unconscious","unresponsive","collapsed","bleeding","bleed","blood",
    "cardiac","pulse","heartbeat","palpitation","convulsing","convulsion",
    "stabbed","stabbing","fracture","broken","injury","injured",
    "burning","burnt","burn","pain","pains","ache","hurting","hurt",
    "chest","tightness","pressure","dizzy","dizziness","nausea","vomiting",
    "trapped","stuck","smoke","fire","flames","accident","crash","collision",
    "shot","shooting","assault","underwater","submerged","critical","emergency",
    "ambulance","hospital","police","rescue","help","responsive",
    "behosh","dard","khoon","aag","chot",
    "theft","thief","stolen","robbery","burglary","mugging","snatching",
    "pickpocket","trespassing","vandalism","chor","chori","dakaiti","loot",
]

def correct_transcript(text):
    t = text.lower().strip()
    if not t:
        return text
    for wrong, right in sorted(PHONETIC_MAP.items(), key=lambda x: len(x[0]), reverse=True):
        if wrong in t:
            t = t.replace(wrong, right)
    MAP_KEYS = list(PHONETIC_MAP.keys())
    words    = t.split()
    replaced = [False] * len(words)
    for n in range(4, 0, -1):
        i = 0
        while i <= len(words) - n:
            if any(replaced[i:i+n]):
                i += 1; continue
            gram = " ".join(words[i:i+n])
            hits = difflib.get_close_matches(gram, MAP_KEYS, n=1, cutoff=0.75)
            if hits:
                cw = PHONETIC_MAP[hits[0]].split()
                words    = words[:i] + cw + words[i+n:]
                replaced = replaced[:i] + [True]*len(cw) + replaced[i+n:]
                i += len(cw)
            else:
                i += 1
    corrected = []
    for word in " ".join(words).split():
        clean = word.strip(".,!?;:")
        if clean in NLP_VOCAB or len(clean) <= 2:
            corrected.append(word); continue
        hits = difflib.get_close_matches(clean, NLP_VOCAB, n=1, cutoff=0.82)
        if hits and hits[0] != clean:
            corrected.append(hits[0] + word[len(clean):])
        else:
            corrected.append(word)
    return " ".join(corrected)


#geolocation
GEO_PORT  = 5050
_GEO_PORTS_TO_TRY = [5050, 5051, 5052, 5053, 8765, 9001]
_geo_data = {"lat": None, "lon": None, "accuracy": None,
             "ready": False, "fallback": False, "source": "none"}
_geo_lock = threading.Lock()
_active_geo_port = None   # set by start_geo_server()

# The HTML uses window.location redirect (GET) — universally supported,
# never blocked by browser security policy unlike fetch()/XHR to localhost.
def _make_geo_html(port):
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"/>
<title>AideDispatch — Location</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#080c14;color:#e2e8f8;font-family:'Segoe UI',sans-serif;
     display:flex;align-items:center;justify-content:center;height:100vh}}
.card{{background:#0d1421;border:1px solid #1a2744;border-radius:14px;
      padding:36px 44px;text-align:center;max-width:440px;width:92%}}
h1{{color:#ff2d55;font-size:1.9rem;letter-spacing:3px;margin-bottom:6px}}
p{{color:#5a6a8a;font-size:.9rem;margin:4px 0}}
.status{{font-size:1rem;margin:18px 0;min-height:28px}}
.coords{{font-family:monospace;font-size:.85rem;color:#30d158;
        background:#0a0f1c;padding:10px 14px;border-radius:6px;
        margin:10px 0;display:none}}
.err{{color:#ff9f0a;font-size:.85rem;margin-top:10px;display:none}}
.pulse{{display:inline-block;width:9px;height:9px;background:#ff2d55;
       border-radius:50%;animation:p 1.2s infinite;margin-right:7px;vertical-align:middle}}
@keyframes p{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:.3;transform:scale(.7)}}}}
.skipbtn{{margin-top:18px;padding:8px 18px;background:#1a2744;color:#e9c46a;
          border:1px solid #2a3a6a;border-radius:6px;cursor:pointer;font-size:.85rem}}
.skipbtn:hover{{background:#243a7a}}
</style>
</head>
<body>
<div class="card">
  <h1>⚡ AIDE<span style="color:#e2e8f8">DISPATCH</span></h1>
  <p>Emergency Engine — Location Capture</p>
  <div class="status" id="st"><span class="pulse"></span>Requesting GPS location…</div>
  <div class="coords" id="co"></div>
  <div class="err"   id="er"></div>
  <button class="skipbtn" onclick="useDefault()">Skip — use default location</button>
</div>
<script>
var sent = false;
function send(lat, lon, acc, fallback) {{
  if (sent) return;
  sent = true;
  // Use GET redirect — works even when fetch/XHR is blocked to localhost
  var params = 'lat='+lat+'&lon='+lon+'&acc='+(acc||0)+'&fb='+(fallback?1:0);
  var img = new Image();   // fire-and-forget GET, no CORS issues
  img.src = 'http://127.0.0.1:{port}/loc?' + params;
  img.onerror = img.onload = function() {{}};
  if (fallback) {{
    document.getElementById('st').innerHTML =
      '<span style="color:#ff9f0a">⚠ Using default location</span>';
    document.getElementById('er').style.display = 'block';
    document.getElementById('er').textContent = 'Default: Koramangala, Bengaluru';
  }} else {{
    document.getElementById('st').innerHTML =
      '<span style="color:#30d158">✓ Location captured!</span>';
    document.getElementById('co').style.display = 'block';
    document.getElementById('co').textContent =
      'Lat: '+lat.toFixed(6)+'  Lon: '+lon.toFixed(6)+'  ±'+Math.round(acc||0)+'m';
    setTimeout(function(){{ window.close(); }}, 2000);
  }}
}}
function useDefault() {{
  send(12.9352, 77.6244, 0, true);
}}
if (!navigator.geolocation) {{
  useDefault();
}} else {{
  navigator.geolocation.getCurrentPosition(
    function(p) {{
      send(p.coords.latitude, p.coords.longitude, p.coords.accuracy, false);
    }},
    function(e) {{
      var m = {{1:'Permission denied.',2:'Position unavailable.',3:'Timed out.'}};
      document.getElementById('er').style.display = 'block';
      document.getElementById('er').textContent = m[e.code] || 'GPS error — using default.';
      useDefault();
    }},
    {{enableHighAccuracy: true, timeout: 12000, maximumAge: 0}}
  );
}}
// Auto-fallback after 20s in case browser blocks entirely
setTimeout(function() {{ if (!sent) useDefault(); }}, 20000);
</script>
</body>
</html>"""


class _GeoHandler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass   # suppress console spam

    def do_GET(self):
        if self.path.startswith("/loc?"):
            # Parse GET params — the browser sends coords via Image() GET
            try:
                qs = self.path[5:]   # strip "/loc?"
                params = {}
                for part in qs.split("&"):
                    k, _, v = part.partition("=")
                    params[k] = v
                lat = float(params["lat"])
                lon = float(params["lon"])
                acc = float(params.get("acc", 0)) or None
                fb  = params.get("fb", "0") == "1"
                with _geo_lock:
                    _geo_data.update(lat=lat, lon=lon, accuracy=acc,
                                     fallback=fb, ready=True,
                                     source="browser-gps" if not fb else "browser-default")
            except Exception:
                pass
            # Return 1x1 transparent GIF so browser Image() doesn't error-log
            self.send_response(200)
            self.send_header("Content-Type", "image/gif")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00"
                             b"\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21"
                             b"\xf9\x04\x00\x00\x00\x00\x00\x2c\x00\x00"
                             b"\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b")
        else:
            # Serve the HTML page
            port = _active_geo_port or GEO_PORT
            html = _make_geo_html(port).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)


def start_geo_server():
    """Try multiple ports; return the one that worked, or None."""
    global _active_geo_port
    for port in _GEO_PORTS_TO_TRY:
        try:
            srv = HTTPServer(("127.0.0.1", port), _GeoHandler)
            srv.daemon_threads = True
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            _active_geo_port = port
            time.sleep(0.15)   # give thread a moment to bind
            return srv, port
        except OSError:
            continue
    _active_geo_port = None
    return None, None



#  GEO MATH  (v1 + v2)


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0; r = math.pi / 180
    dlat = (lat2 - lat1) * r; dlon = (lon2 - lon1) * r
    a = math.sin(dlat/2)**2 + math.cos(lat1*r)*math.cos(lat2*r)*math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))

# Alias for v2 compat
haversine_distance = haversine

def bearing(lat1, lon1, lat2, lon2):
    r = math.pi / 180; dlon = (lon2 - lon1) * r
    x = math.sin(dlon) * math.cos(lat2*r)
    y = math.cos(lat1*r)*math.sin(lat2*r) - math.sin(lat1*r)*math.cos(lat2*r)*math.cos(dlon)
    return (math.atan2(x, y) * 180 / math.pi) % 360

def geo_to_canvas(lat, lon, ref_lat, ref_lon, zoom, cx, cy):
    kpd_lat = 111.0; kpd_lon = 111.0 * math.cos(ref_lat * math.pi / 180)
    dx = (lon - ref_lon) * kpd_lon * zoom
    dy = (ref_lat - lat) * kpd_lat * zoom
    return cx + dx, cy + dy


def get_current_location():
    """Quick IP-based location — no browser needed, ~200 ms."""
    try:
        with urllib.request.urlopen(
                "http://ip-api.com/json/?fields=lat,lon,status", timeout=3) as r:
            d = json.loads(r.read())
            if d.get("status") == "success":
                return d["lat"], d["lon"]
    except Exception:
        pass
    return None



#  DATA 


UNITS = [
    {"id":"AMB-01",  "type":"Ambulance",   "status":"Available", "location":"Koramangala", "lat":12.9352, "lon":77.6245, "distance":0.0},
    {"id":"AMB-02",  "type":"Ambulance",   "status":"Available", "location":"Indiranagar", "lat":12.9784, "lon":77.6408, "distance":0.0},
    {"id":"AMB-03",  "type":"Ambulance",   "status":"Deployed",  "location":"HSR Layout",  "lat":12.9116, "lon":77.6389, "distance":0.0},
    {"id":"FIRE-01", "type":"Fire Engine", "status":"Available", "location":"MG Road",     "lat":12.9756, "lon":77.6197, "distance":0.0},
    {"id":"FIRE-02", "type":"Fire Engine", "status":"Deployed",  "location":"Whitefield",  "lat":12.9698, "lon":77.7499, "distance":0.0},
    {"id":"POL-01",  "type":"Police",      "status":"Available", "location":"BTM Layout",  "lat":12.9166, "lon":77.6101, "distance":0.0},
    {"id":"POL-02",  "type":"Police",      "status":"Available", "location":"Jayanagar",   "lat":12.9299, "lon":77.5826, "distance":0.0},
]

DISPATCH_RULES = {
    "Cardiac":         ["Ambulance"],
    "Stroke":          ["Ambulance"],
    "Severe Bleeding": ["Ambulance"],
    "Fracture":        ["Ambulance"],
    "Head Injury":     ["Ambulance"],
    "Seizure":         ["Ambulance"],
    "Choking":         ["Ambulance"],
    "Anaphylaxis":     ["Ambulance"],
    "Asthma":          ["Ambulance"],
    "Poisoning":       ["Ambulance"],
    "Drowning":        ["Ambulance"],
    "Burns":           ["Ambulance"],
    "Fire":            ["Fire Engine", "Ambulance"],
    "Accident":        ["Ambulance", "Police"],
    "Assault":         ["Police", "Ambulance"],
    "Theft":           ["Police"],
    "General":         ["Ambulance"],
}

BYSTANDER_SCRIPTS = {
    "Cardiac":         ["Check responsiveness and breathing.", "Call for CPR-trained help immediately.",
                        "Start chest compressions (100-120 per minute).", "Push hard and fast in center of chest.",
                        "Use AED if available.", "Continue until help arrives."],
    "Stroke":          ["Note time symptoms started.", "Keep patient sitting upright.",
                        "Do NOT give food or water.", "Monitor breathing.",
                        "Stay calm and reassure.", "Prepare for rapid hospital transport."],
    "Severe Bleeding": ["Apply firm pressure with cloth.", "Do NOT remove embedded objects.",
                        "Elevate injured area if possible.", "Apply bandage tightly.",
                        "Keep person lying down.", "Watch for shock signs."],
    "Fracture":        ["Do NOT move injured limb.", "Immobilize using splint.",
                        "Apply cold pack.", "Control bleeding if present.",
                        "Keep patient still.", "Wait for ambulance."],
    "Head Injury":     ["Do NOT move neck.", "Keep head supported.",
                        "Monitor consciousness.", "Control bleeding gently.",
                        "Do NOT give food.", "Watch for vomiting."],
    "Seizure":         ["Do NOT restrain.", "Move objects away.",
                        "Place something soft under head.", "Turn person on side after seizure.",
                        "Do NOT put anything in mouth.", "Time the seizure."],
    "Choking":         ["Ask if they can cough.", "Give 5 back blows.",
                        "Give 5 abdominal thrusts.", "Repeat until object removed.",
                        "If unconscious, start CPR.", "Call emergency services."],
    "Anaphylaxis":     ["Use epinephrine auto-injector.", "Lay person flat.",
                        "Loosen tight clothing.", "Monitor breathing.",
                        "Prepare CPR if needed.", "Stay with patient."],
    "Asthma":          ["Help use inhaler.", "Sit upright.",
                        "Loosen tight clothes.", "Encourage slow breathing.",
                        "Repeat inhaler after 5 mins.", "Call if no improvement."],
    "Poisoning":       ["Do NOT induce vomiting.", "Identify substance.",
                        "Check breathing.", "Keep person conscious.",
                        "Save container for doctors.", "Call poison center."],
    "Drowning":        ["Remove from water safely.", "Check breathing.",
                        "Start CPR if needed.", "Remove wet clothes.",
                        "Keep warm.", "Monitor closely."],
    "Burns":           ["Cool burn with water 20 mins.", "Do NOT apply ice.",
                        "Remove tight items.", "Cover with sterile cloth.",
                        "Do NOT burst blisters.", "Seek medical care."],
    "Fire":            ["Use stairs only.", "Stay low under smoke.",
                        "Cover nose with cloth.", "Check doors before opening.",
                        "Move to safe area.", "Do NOT re-enter building."],
    "Accident":        ["Ensure scene safety.", "Do NOT move victim.",
                        "Control bleeding.", "Check breathing.",
                        "Keep warm.", "Wait for ambulance."],
    "Assault":         ["Move away from attacker to a safe place.", "Do NOT fight back unless no other option.",
                        "Apply pressure to any wounds with a clean cloth.", "Do NOT disturb the scene.",
                        "Note attacker description: clothes, height, direction fled.", "Stay on the line — police are coming."],
    "Theft":           ["Do NOT chase or confront the suspect.", "Note suspect description and direction fled.",
                        "Do NOT touch anything the suspect handled (preserve evidence).", "Note any vehicle details (make, colour, plate).",
                        "Keep bystanders away from the scene.", "Wait for police — they are on the way."],
    "General":         ["Keep patient calm.", "Monitor breathing.",
                        "Do not give food.", "Keep warm.",
                        "Stay on the line.", "Wait for help."],
}

CRITICAL_HIGHLIGHT = [
    "not breathing","cant breathe","can't breathe","stopped breathing",
    "no pulse","low pulse","weak pulse","faint pulse","no heartbeat","heart stopped",
    "unconscious","unresponsive","not responding","wont wake","won't wake",
    "not moving","stopped moving","no signs of life",
    "heavy bleeding","bleeding badly","blood everywhere","losing blood",
    "collapsed","fallen unconscious","passed out",
    "seizure","convulsing","fitting",
    "choking","turning blue","lips blue","face blue",
    "trapped","cant get out","can't get out",
    "heart attack","cardiac","cardiac arrest",
    "drowning","submerged","underwater",
    "severe burns","on fire",
    "behosh","saas nahi","dhadkan nahi","khoon",
    "kidnapping","hostage","abducted","gunshot","gun","armed robbery","dakaiti",
]

MODERATE_HIGHLIGHT = [
    "bleeding","blood","pain","chest pain","chest tightness","chest pressure",
    "dizzy","confused","short of breath","shortness of breath","can't breathe",
    "fell","injured","hurt","vomiting","nausea","smoke","fire","crash","accident",
    "breathing difficulty","breathless","fracture","broken bone","head injury","burn",
    "dard","chot","gir gaya","seene mein dard",
]

CRITICAL_SCORED = [
    ("not breathing",10),("cant breathe",10),("can't breathe",10),("stopped breathing",10),
    ("short of breath",6),("shortness of breath",6),("chest pain",6),("chest tightness",6),("chest pressure",6),
    ("no pulse",10),("low pulse",10),("weak pulse",10),("faint pulse",10),("pulse is low",10),("pulse is weak",10),
    ("no heartbeat",10),("heart stopped",10),("cardiac arrest",10),
    ("unconscious",8),("unresponsive",8),("not responding",8),("wont wake",8),("won't wake",8),
    ("not moving",7),("stopped moving",7),("no signs of life",10),
    ("heavy bleeding",8),("bleeding badly",7),("blood everywhere",7),("losing blood",7),
    ("collapsed",7),("passed out",7),("fallen unconscious",8),
    ("seizure",8),("convulsing",8),("fitting",7),("choking",9),
    ("turning blue",9),("lips blue",9),("face blue",8),("trapped",7),
    ("heart attack",8),("cardiac",6),("drowning",9),("submerged",8),("underwater",7),
    ("severe burns",8),("fire spreading",8),("building on fire",9),("house on fire",9),
    ("behosh",8),("saas nahi",10),("dhadkan nahi",10),
    ("kidnapping",9),("hostage",9),("abducted",9),("gun",7),("gunshot",9),
]

DOWNGRADE_WORDS = [
    ("conscious",-3),("is breathing",-4),("breathing fine",-5),("stable",-4),
    ("walking",-3),("talking",-3),("alert",-3),("minor",-2),("small cut",-2),("bruise",-1),
]

TYPE_MIN_SEVERITY = {
    "Cardiac":"CRITICAL","Stroke":"CRITICAL","Severe Bleeding":"CRITICAL",
    "Choking":"CRITICAL","Anaphylaxis":"CRITICAL","Drowning":"CRITICAL",
    "Head Injury":"MODERATE","Seizure":"MODERATE","Asthma":"MODERATE",
    "Poisoning":"MODERATE","Burns":"MODERATE","Fracture":"LOW",
    "Fire":"MODERATE","Accident":"MODERATE","Assault":"MODERATE","Theft":"LOW","General":"LOW",
}

TYPE_KEYWORDS = {
    "Cardiac":["heart","pulse","chest pain","chest tightness","chest pressure","chest heaviness",
               "cardiac","heartbeat","not breathing","cpr","collapsed","breathe","heart attack",
               "palpitation","heart stopped","short of breath","shortness of breath","can't breathe",
               "no pulse","low pulse","weak pulse","no heartbeat","cardiac arrest","heart rate",
               "heart racing","seene mein dard","sine mein dard","behosh","saas nahi","dhadkan nahi","dhadkan band"],
    "Stroke":["stroke","facial droop","arm weakness","speech slurred","sudden numbness",
              "sudden confusion","balance loss"],
    "Severe Bleeding":["heavy bleeding","bleeding badly","blood everywhere","losing blood",
                       "deep cut","severed","artery"],
    "Fracture":["fracture","broken bone","broken arm","broken leg","bone sticking",
                "deformity","can't move limb"],
    "Head Injury":["head injury","hit head","skull","concussion","head bleeding",
                   "head trauma","knocked head"],
    "Seizure":["seizure","convulsion","fitting","convulsing","epilepsy","shaking uncontrollably"],
    "Choking":["choking","choked","airway blocked","something stuck","can't swallow","turning blue"],
    "Anaphylaxis":["anaphylaxis","allergic reaction","severe allergy","throat swelling",
                   "bee sting allergy","epipen"],
    "Asthma":["asthma","asthma attack","inhaler","wheezing","can't breathe asthma","bronchospasm"],
    "Poisoning":["poisoning","overdose","swallowed poison","toxic","chemical ingestion","drug overdose"],
    "Fire":["fire","burning","smoke","flames","blaze","burnt","explosion","gas leak",
            "building on fire","house fire","aag"],
    "Drowning":["drown","drowning","water","river","lake","pool","submerged","underwater",
                "fell in water","swept away","flood","pani mein"],
    "Burns":["burn","burns","scalded","scald","chemical burn","fire burn","severe burn"],
    "Accident":["accident","crash","collision","hit","vehicle","car","bike","truck","bus","road",
                "fell","fall","motorcycle","auto","overturned","skid","durghatna"],
    "Assault":  ["attack","assault","stabbed","stab","shot","shooting","gun","gunshot","violence",
                "fight","knife","weapon","beaten","hit by person","murdered","murder",
                "threatening","threatened","hostage","kidnap","kidnapping","abduction","abducted",
                "harassment","molested","sexual assault","eve teasing","rape"],
    "Theft":    ["theft","thief","thieves","steal","stole","stealing","stolen","robbed","robbery",
                "burglary","burglar","pickpocket","snatching","snatched","chain snatching",
                "bag snatching","mugging","mugged","mug","shoplifting","looting","looted",
                "broke in","breaking in","trespassing","vandalism","car theft","bike theft",
                "house break","chor","chori","churaya","loot","lootna","ghar mein ghusa",
                "dakaiti","dakait","mobile churaya","wallet stolen","purse snatched",
                "vehicle stolen","my car stolen","my bike stolen","took my","took her",
                "stole my","stole her","snatched my","snatched her","ran away with",
                "broke into","entered house","unauthorized","intruder","trespasser"],
}

CONTRADICTIONS = [
    (["unconscious","unresponsive","not responding"],
     ["talking","speaking","shouting","walking"],
     "Caller says unconscious BUT also responsive — clarify"),
    (["not breathing","stopped breathing"],["breathing","can breathe"],
     "Conflicting breathing status — re-confirm with caller"),
    (["no pulse","no heartbeat"],["has pulse","pulse is there"],
     "Conflicting pulse status — re-confirm immediately"),
    (["one person","1 person","alone"],["multiple","many people","several","crowd"],
     "Victim count conflict — confirm exact number"),
]

CHECKLIST_ITEMS = ["Location confirmed?","Number of victims?","Victim conscious?",
                   "Victim breathing?","Caller safe?","Landmark given?"]

CHECKLIST_AUTO_TRIGGERS = {
    0:{"keywords":["at ","near ","in ","on ","outside ","road","street","nagar","layout",
                   "circle","junction","hospital","school","mall","park","gate","cross","main"],"min_hits":1},
    1:{"keywords":["one person","a man","a woman","a person","someone","1 person","2 people","3 people",
                   "multiple","several","many people","two","three","four","five","passenger","victim","injured","people"],"min_hits":1},
    2:{"keywords":["conscious","unconscious","awake","asleep","responding","not responding","responsive",
                   "unresponsive","talking","speaking","eyes open","eyes closed","behosh","wont wake"],"min_hits":1},
    3:{"keywords":["breathing","not breathing","stopped breathing","breathe","can't breathe","short of breath",
                   "gasping","saas nahi","no breathing","chest moving","shallow breath"],"min_hits":1},
    4:{"keywords":["i am safe","i'm safe","i am okay","i'm okay","not safe","i am fine","i'm fine",
                   "safe","danger","bystander","passing by","outside"],"min_hits":1},
    5:{"keywords":["near ","next to","opposite","behind","in front of","beside","landmark","temple","mosque",
                   "church","petrol pump","signal","flyover","bridge","metro","bus stop","atm","hospital",
                   "school","college"],"min_hits":1},
}

LOG_FILE = "incident_log.csv"
OVERLOAD_WARNING_SECONDS = 45


#  LOGIC FUNCTIONS

def classify_type(text):
    text = text.lower(); scores = {e: 0 for e in TYPE_KEYWORDS}
    for etype, kws in TYPE_KEYWORDS.items():
        for kw in kws:
            if kw in text: scores[etype] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "General"

def classify_severity(text, emergency_type="General"):
    t = text.lower(); score = 0; matched_spans = []
    for phrase, weight in sorted(CRITICAL_SCORED, key=lambda x: len(x[0]), reverse=True):
        idx = t.find(phrase)
        if idx != -1:
            span = (idx, idx + len(phrase))
            if not any(s[0] <= span[0] and span[1] <= s[1] for s in matched_spans):
                score += weight; matched_spans.append(span)
    for phrase, weight in DOWNGRADE_WORDS:
        idx = t.find(phrase)
        if idx != -1:
            ctx = t[max(0, idx-10):idx]
            if not any(n in ctx for n in ["not ","no ","isn't","isnt","cant","can't"]):
                score += weight
    min_sev = TYPE_MIN_SEVERITY.get(emergency_type, "LOW")
    severity = "CRITICAL" if score >= 7 else "MODERATE" if score >= 4 else "LOW"
    order = ["LOW","MODERATE","CRITICAL"]
    if order.index(severity) < order.index(min_sev):
        severity = min_sev
    return severity, {"CRITICAL":1,"MODERATE":2,"LOW":3}[severity]

def find_unit(emergency_type):
    needed = DISPATCH_RULES.get(emergency_type, ["Ambulance"])
    for utype in needed:
        for u in UNITS:
            if u["type"] == utype and u["status"] == "Available":
                return u
    return None

def find_nearest_unit(units, emergency_type, inc_lat, inc_lon):
    needed = DISPATCH_RULES.get(emergency_type, ["Ambulance"])
    best, best_d = None, float("inf")
    for utype in needed:
        for u in units:
            if u["type"] == utype and u["status"] == "Available":
                d = haversine(inc_lat, inc_lon, u["lat"], u["lon"])
                if d < best_d:
                    best_d, best = d, u
    if best:
        return best, round(best_d, 2), round((best_d / 40) * 60, 1)
    return None

def dispatch_unit(u): u["status"] = "Deployed"
def reset_unit(u):    u["status"] = "Available"

def extract_summary(text):
    summary = {"location":"Not mentioned","victims":"Not mentioned",
               "caller":"Not mentioned","condition":"Not mentioned"}
    t = text.lower()
    for pat in [r"at (.{3,30})",r"near (.{3,30})",r"on (.{3,20} road)",
                r"in (.{3,20})",r"outside (.{3,30})"]:
        m = re.search(pat, t)
        if m: summary["location"] = m.group(1).strip().title()[:30]; break
    for pat in [r"(\d+) people",r"(\d+) persons",r"(\d+) victims",
                r"(\d+) injured",r"(\d+) passengers"]:
        m = re.search(pat, t)
        if m: summary["victims"] = m.group(1); break
    else:
        if any(w in t for w in ["a man","a woman","a person","one person","someone"]):
            summary["victims"] = "1"
        elif any(w in t for w in ["multiple","several","many"]):
            summary["victims"] = "Multiple"
    if any(w in t for w in ["i am","i'm","my","myself"]):           summary["caller"] = "Involved"
    elif any(w in t for w in ["bystander","passing by","witness"]): summary["caller"] = "Bystander"
    else:                                                            summary["caller"] = "Unknown"
    conds = []
    if any(w in t for w in ["not breathing","stopped breathing","saas nahi"]): conds.append("Not breathing")
    if any(w in t for w in ["no pulse","low pulse","weak pulse","dhadkan nahi"]): conds.append("Low/No pulse")
    if any(w in t for w in ["unconscious","unresponsive","behosh","passed out"]): conds.append("Unconscious")
    if any(w in t for w in ["bleeding","blood","khoon"]):                         conds.append("Bleeding")
    if any(w in t for w in ["chest pain","chest tightness","seene mein dard"]):   conds.append("Chest pain")
    if any(w in t for w in ["short of breath","can't breathe"]):                  conds.append("Breathing difficulty")
    if any(w in t for w in ["conscious","awake","talking"]):                       conds.append("Conscious")
    if any(w in t for w in ["breathing"]) and "Not breathing" not in conds:       conds.append("Breathing")
    summary["condition"] = ", ".join(conds) if conds else "Unknown"
    return summary

def detect_contradictions(text):
    t = text.lower(); warnings = []
    for a, b, msg in CONTRADICTIONS:
        if any(kw in t for kw in a) and any(kw in t for kw in b):
            warnings.append(msg)
    return warnings

def log_incident(etype, severity, uid):
    exists = os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(["Timestamp","Type","Severity","Unit Dispatched"])
        w.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), etype, severity, uid])


#  COLOUR PALETTE  

C = {
    "bg":      "#0d1117",
    "surface": "#161b22",
    "surface2":"#1c2330",
    "border":  "#30363d",
    "accent":  "#238636",
    "danger":  "#da3633",
    "warn":    "#d29922",
    "info":    "#1f6feb",
    "text":    "#e6edf3",
    "muted":   "#8b949e",
    "tag_red": "#ff7b72",
    "tag_amb": "#e3b341",
    "green":   "#3fb950",
    "header":  "#da3633",
}
# Map-specific colours (used in canvas drawing)
MAP_BG   = "#0a0e18"
GRID_COL = "#111a2e"
ROAD_COL = "#1e3260"
MAP_RED  = "#e63946"
MAP_AMB  = "#e9c46a"
MAP_GRN  = "#00ff88"
MAP_BLUE = "#457b9d"


#  SPLASH SCREEN  — robust, multi-path, auto-timeout

SPLASH_TIMEOUT = 18   # seconds before hard fallback kicks in

class SplashScreen:
    """
    Shows while geolocation is being acquired.
    Three parallel strategies run simultaneously:
      1. Browser GPS page (most accurate)
      2. ip-api.com (fast, no browser needed)
      3. Hard timeout auto-fallback after SPLASH_TIMEOUT seconds
    Whichever finishes first wins.
    """
    DEFAULT_LAT = 12.9352
    DEFAULT_LON = 77.6244

    def __init__(self, root, geo_port):
        self.root     = root
        self.geo_port = geo_port
        self.root.title("AideDispatch — Acquiring Location")
        self.root.configure(bg="#080c14")
        self.root.geometry("480x360")
        self.root.resizable(False, False)
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"480x360+{(sw-480)//2}+{(sh-360)//2}")

        self._done        = False
        self._dots        = 0
        self._countdown   = SPLASH_TIMEOUT

        self._build()
        self._tick_anim()
        self._tick_countdown()
        # Poll for GPS result
        self.root.after(300, self._poll)
        # Also try ip-api in background thread
        if geo_port:
            threading.Thread(target=self._try_ip_api, daemon=True).start()

    def _build(self):
        tk.Label(self.root, text="⚡ AideDispatch",
                 font=("Helvetica", 22, "bold"),
                 bg="#080c14", fg="#ff2d55").pack(pady=(28, 4))
        tk.Label(self.root, text="Human-Assist Emergency Engine",
                 font=("Helvetica", 10),
                 bg="#080c14", fg="#5a6a8a").pack()
        tk.Frame(self.root, bg="#1a2744", height=1).pack(fill="x", padx=36, pady=14)

        self.status_lbl = tk.Label(self.root,
            text="Acquiring your location…",
            font=("Helvetica", 11), bg="#080c14", fg="#e9c46a")
        self.status_lbl.pack()

        self.dots_lbl = tk.Label(self.root, text="",
            font=("Courier", 13), bg="#080c14", fg="#e9c46a")
        self.dots_lbl.pack(pady=3)

        self.source_lbl = tk.Label(self.root,
            text="Trying: Browser GPS  |  ip-api",
            font=("Helvetica", 9), bg="#080c14", fg="#3a4a6a")
        self.source_lbl.pack()

        self.coords_lbl = tk.Label(self.root, text="",
            font=("Courier", 9), bg="#080c14", fg="#30d158", wraplength=400)
        self.coords_lbl.pack(pady=5)

        tk.Frame(self.root, bg="#1a2744", height=1).pack(fill="x", padx=36, pady=8)

        # Countdown row
        ctr = tk.Frame(self.root, bg="#080c14"); ctr.pack()
        tk.Label(ctr, text="Auto-skip in ",
                 font=("Helvetica", 9), bg="#080c14", fg="#5a6a8a").pack(side="left")
        self.countdown_lbl = tk.Label(ctr, text=f"{SPLASH_TIMEOUT}s",
            font=("Helvetica", 9, "bold"), bg="#080c14", fg="#e9c46a")
        self.countdown_lbl.pack(side="left")
        tk.Label(ctr, text="  or  ",
                 font=("Helvetica", 9), bg="#080c14", fg="#5a6a8a").pack(side="left")
        tk.Button(ctr, text="Skip now & use default",
                  font=("Helvetica", 9), bg="#1a2744", fg="#e9c46a",
                  relief="flat", cursor="hand2", padx=8, pady=3,
                  command=self._force_fallback).pack(side="left")

        # If server failed to start, show a direct-start button
        if not self.geo_port:
            tk.Frame(self.root, bg="#3a0a0a", height=1).pack(fill="x", padx=36, pady=4)
            tk.Label(self.root,
                text="⚠ Could not start location server.\nUsing default location.",
                font=("Helvetica", 9), bg="#080c14", fg="#ff9f0a", justify="center"
            ).pack()
            self.root.after(1500, self._force_fallback)

    def _tick_anim(self):
        if self._done: return
        self._dots = (self._dots + 1) % 4
        self.dots_lbl.config(text="●" * self._dots + "○" * (3 - self._dots))
        self.root.after(400, self._tick_anim)

    def _tick_countdown(self):
        if self._done: return
        self._countdown -= 1
        if self._countdown <= 0:
            self._force_fallback(); return
        color = "#ff4d4d" if self._countdown <= 5 else "#e9c46a"
        self.countdown_lbl.config(text=f"{self._countdown}s", fg=color)
        self.root.after(1000, self._tick_countdown)

    def _try_ip_api(self):
        """Run ip-api in background; if it returns first, use it."""
        loc = get_current_location()
        if loc and not self._done:
            lat, lon = loc
            with _geo_lock:
                # Only use if browser GPS hasn't already arrived
                if not _geo_data["ready"]:
                    _geo_data.update(lat=lat, lon=lon, accuracy=None,
                                     fallback=False, ready=True, source="ip-api")

    def _poll(self):
        if self._done: return
        with _geo_lock:
            ready = _geo_data["ready"]
            lat   = _geo_data["lat"]
            lon   = _geo_data["lon"]
            acc   = _geo_data["accuracy"]
            fb    = _geo_data["fallback"]
            src   = _geo_data.get("source","")
        if ready:
            self._on_received(lat, lon, acc, fb, src)
        else:
            self.root.after(250, self._poll)

    def _on_received(self, lat, lon, acc, fallback, source=""):
        if self._done: return
        self._done = True
        # Brief confirmation flash before closing
        if not fallback:
            src_label = {"browser-gps":"Browser GPS","ip-api":"IP Geolocation"}.get(source, source)
            self.status_lbl.config(text=f"✓ Location captured via {src_label}!", fg="#30d158")
            acc_str = f"  ±{int(acc)}m" if acc else ""
            self.coords_lbl.config(text=f"{lat:.5f}, {lon:.5f}{acc_str}")
        else:
            self.status_lbl.config(text="Using default location (Koramangala)", fg="#ff9f0a")
        self.root.after(900, self.root.destroy)

    def _force_fallback(self):
        if self._done: return
        with _geo_lock:
            if not _geo_data["ready"]:
                _geo_data.update(lat=self.DEFAULT_LAT, lon=self.DEFAULT_LON,
                                 accuracy=None, fallback=True, ready=True,
                                 source="manual-skip")
        self._on_received(self.DEFAULT_LAT, self.DEFAULT_LON, None, True, "manual-skip")



#  MAIN APPLICATION  (full merge)

class DispatchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AideDispatch  |  Human-Assist Emergency Engine")
        self.root.configure(bg=C["bg"])
        self.root.geometry("1440x900")
        self.root.minsize(1200, 720)

        # Core state
        self.current_unit    = None
        self.listening       = False
        self.eta_value       = 0
        self.eta_job         = None
        self.overload_job    = None
        self.incident_start  = None
        self.check_vars      = []
        self.check_icons     = []
        self.check_btns      = []
        self._audio_queue    = queue.Queue()
        self._cached_location = None

        # Geolocation state from splash
        with _geo_lock:
            self.caller_lat   = _geo_data["lat"]
            self.caller_lon   = _geo_data["lon"]
            self.caller_acc   = _geo_data["accuracy"]
            self.geo_fallback = _geo_data["fallback"]
            self.geo_ready    = _geo_data["ready"]

        # Map state (v1)
        self.map_zoom        = 60.0
        self.map_pan_x       = 0.0
        self.map_pan_y       = 0.0
        self._map_drag_start = None
        self._map_pulse      = 0.0
        self._map_anim_off   = 0
        self._map_vehicles   = {}
        self._map_routes     = {}
        self._map_dispatched = set()

        self._active_tab = "dispatch"

        self._build_fonts()
        self._build_ui()
        self._refresh_unit_board()
        self._map_animate()
        self._tick_clock()
        # Also start ip-api background fetch for supplemental location
        threading.Thread(target=self._fetch_ip_location, daemon=True).start()
        self.root.after(100, self._on_geo_received)

    # FONTS 

    def _build_fonts(self):
        self.f_title  = tkfont.Font(family="Helvetica", size=16, weight="bold")
        self.f_head   = tkfont.Font(family="Helvetica", size=10, weight="bold")
        self.f_body   = tkfont.Font(family="Helvetica", size=10)
        self.f_small  = tkfont.Font(family="Helvetica", size=9)
        self.f_badge  = tkfont.Font(family="Helvetica", size=12, weight="bold")
        self.f_mono   = tkfont.Font(family="Courier",   size=10)
        self.f_script = tkfont.Font(family="Helvetica", size=11, weight="bold")
        self.f_big    = tkfont.Font(family="Helvetica", size=32, weight="bold")
        self.f_map    = tkfont.Font(family="Courier",   size=9)
        self.f_mapbig = tkfont.Font(family="Courier",   size=22, weight="bold")

    def _fetch_ip_location(self):
        """Background ip-api fetch — updates location if better data arrives."""
        loc = get_current_location()
        if loc:
            self._cached_location = loc
            # If we're still on fallback/default, upgrade to ip-api coords
            if self.geo_fallback or not self.geo_ready:
                lat, lon = loc
                with _geo_lock:
                    _geo_data.update(lat=lat, lon=lon, accuracy=None,
                                     fallback=False, ready=True, source="ip-api")
                self.caller_lat   = lat
                self.caller_lon   = lon
                self.caller_acc   = None
                self.geo_fallback = False
                self.geo_ready    = True
                self.root.after(0, self._on_geo_received)

    #CARD HELPER

    def _card(self, parent, title="", fg_title=None, pady=(0,5), expand=False, fill="x"):
        outer = tk.Frame(parent, bg=C["border"], bd=0)
        outer.pack(fill=fill, expand=expand, pady=pady)
        inner = tk.Frame(outer, bg=C["surface"], bd=0)
        inner.pack(fill=fill, expand=expand, padx=1, pady=1)
        if title:
            hdr = tk.Frame(inner, bg=C["surface2"], height=26)
            hdr.pack(fill="x"); hdr.pack_propagate(False)
            tk.Label(hdr, text=title, font=self.f_head,
                     bg=C["surface2"], fg=fg_title or C["muted"],
                     anchor="w", padx=10).pack(side="left", fill="y")
        return inner

    # UI BUILD

    def _build_ui(self):
        hdr = tk.Frame(self.root, bg=C["header"], height=46)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="⚡  AideDispatch", font=self.f_title,
                 bg=C["header"], fg="white").pack(side="left", padx=16, pady=8)
        tk.Label(hdr, text="Human-Assist Engine  |  Cognitive Overload Reduction  |  Live Geolocation",
                 font=self.f_small, bg=C["header"], fg="#ffcccc").pack(side="left", padx=4)
        self.clock_label = tk.Label(hdr, text="", font=self.f_head,
                                    bg=C["header"], fg="white")
        self.clock_label.pack(side="right", padx=16)

        self.overload_bar = tk.Frame(self.root, bg=C["warn"], height=28)
        self.overload_label = tk.Label(self.overload_bar,
            text="⚠  COGNITIVE ALERT — No dispatch in 45s. Act now.",
            font=self.f_head, bg=C["warn"], fg="#0d1117")
        self.overload_label.pack(pady=4)

        self.nlp_bar = tk.Frame(self.root, bg=C["surface2"], height=20)
        self.nlp_bar.pack(fill="x"); self.nlp_bar.pack_propagate(False)
        self.nlp_status = tk.Label(self.nlp_bar, text="", font=self.f_small,
                                   bg=C["surface2"], fg=C["muted"])
        self.nlp_status.pack(side="left", padx=10)

        self._build_tab_bar()

    def _build_tab_bar(self):
        self.tab_bar = tk.Frame(self.root, bg="#0d1117", height=36)
        self.tab_bar.pack(fill="x"); self.tab_bar.pack_propagate(False)
        self._tab_btns   = {}
        self._tab_frames = {}
        for name, label in [("dispatch","🚨  Dispatch"), ("map","🗺  Live Map")]:
            btn = tk.Button(self.tab_bar, text=label, font=self.f_body,
                            bg="#0d1117", fg=C["muted"], relief="flat",
                            cursor="hand2", padx=18,
                            command=lambda n=name: self._switch_tab(n))
            btn.pack(side="left")
            self._tab_btns[name] = btn

        self.geo_pill = tk.Label(self.tab_bar, text="⏳ Waiting for GPS…",
                                 font=self.f_small, bg="#0d1117", fg=C["warn"])
        self.geo_pill.pack(side="right", padx=16)

        self.content = tk.Frame(self.root, bg=C["bg"])
        self.content.pack(fill="both", expand=True)

        f_dispatch = tk.Frame(self.content, bg=C["bg"])
        f_map      = tk.Frame(self.content, bg=MAP_BG)
        self._tab_frames["dispatch"] = f_dispatch
        self._tab_frames["map"]      = f_map

        self._build_dispatch_tab(f_dispatch)
        self._build_map_tab(f_map)
        self._switch_tab("dispatch")

    def _switch_tab(self, name):
        self._active_tab = name
        for n, f in self._tab_frames.items(): f.pack_forget()
        for n, b in self._tab_btns.items():
            b.config(bg="#0d1117" if n != name else C["surface"],
                     fg=C["muted"] if n != name else C["text"])
        self._tab_frames[name].pack(fill="both", expand=True)

    #  DISPATCH TAB 

    def _build_dispatch_tab(self, parent):
        main = tk.Frame(parent, bg=C["bg"])
        main.pack(fill="both", expand=True, padx=8, pady=6)
        col_l = tk.Frame(main, bg=C["bg"])
        col_m = tk.Frame(main, bg=C["bg"])
        col_r = tk.Frame(main, bg=C["bg"])
        col_l.pack(side="left", fill="both", expand=True, padx=(0,3))
        col_m.pack(side="left", fill="both", padx=3)
        col_r.pack(side="right", fill="both", expand=True, padx=(3,0))
        col_m.config(width=300); col_m.pack_propagate(False)
        self._build_left(col_l)
        self._build_mid(col_m)
        self._build_right(col_r)

    def _build_left(self, parent):
        tc = self._card(parent, "CALLER TRANSCRIPT", fg_title=C["info"])
        btn_row = tk.Frame(tc, bg=C["surface"]); btn_row.pack(fill="x", padx=8, pady=(6,4))
        self.mic_btn = tk.Button(btn_row, text="🎙  LISTEN", font=self.f_head,
                                 bg=C["info"], fg="white", relief="flat",
                                 cursor="hand2", padx=12, pady=4, command=self._toggle_listening)
        self.mic_btn.pack(side="left")
        self.mic_status = tk.Label(btn_row, text="Idle", font=self.f_small,
                                   bg=C["surface"], fg=C["muted"])
        self.mic_status.pack(side="left", padx=10)

        self.transcript_box = tk.Text(tc, height=7, font=self.f_mono,
                                      bg=C["surface2"], fg=C["text"],
                                      insertbackground=C["text"],
                                      relief="flat", bd=0, wrap="word", padx=6, pady=4)
        self.transcript_box.pack(fill="x", padx=8, pady=(0,4))
        self.transcript_box.tag_config("critical", foreground=C["tag_red"],
                                       font=tkfont.Font(family="Courier", size=10, weight="bold"))
        self.transcript_box.tag_config("moderate", foreground=C["tag_amb"])

        act_row = tk.Frame(tc, bg=C["surface"]); act_row.pack(fill="x", padx=8, pady=(0,6))
        tk.Button(act_row, text="🚨 ANALYSE", font=self.f_head, bg=C["danger"], fg="white",
                  relief="flat", cursor="hand2", padx=10, pady=4,
                  command=self._run_pipeline).pack(side="left")
        tk.Button(act_row, text="🔄 New Incident", font=self.f_body, bg=C["accent"], fg="white",
                  relief="flat", cursor="hand2", padx=8, pady=4,
                  command=self._new_incident).pack(side="left", padx=6)
        tk.Button(act_row, text="Clear", font=self.f_small, bg=C["surface2"], fg=C["muted"],
                  relief="flat", cursor="hand2", padx=6, pady=4,
                  command=lambda: self.transcript_box.delete("1.0","end")).pack(side="left")

        loc_row = tk.Frame(tc, bg=C["surface"]); loc_row.pack(fill="x", padx=8, pady=(0,8))
        tk.Label(loc_row, text="📍 Caller Location:", font=self.f_small,
                 bg=C["surface"], fg=C["muted"]).pack(side="left")
        self.lbl_caller_loc = tk.Label(loc_row, text="Waiting for GPS…",
                                       font=self.f_small, bg=C["surface"], fg=C["warn"])
        self.lbl_caller_loc.pack(side="left", padx=6)
        tk.Button(loc_row, text="🔄 Get GPS", font=self.f_small,
                  bg=C["surface2"], fg=C["text"], relief="flat", cursor="hand2",
                  padx=6, command=self._re_request_geo).pack(side="right")

        dc = self._card(parent, "DISPATCH OUTPUT", fg_title=C["tag_red"])
        badges = tk.Frame(dc, bg=C["surface"]); badges.pack(fill="x", padx=8, pady=8)
        for label, attr, col in [("TYPE","type_badge",C["info"]),
                                  ("SEVERITY","sev_badge",C["text"]),
                                  ("UNIT","unit_badge",C["green"])]:
            cf = tk.Frame(badges, bg=C["surface"]); cf.pack(side="left", expand=True)
            tk.Label(cf, text=label, font=self.f_small, bg=C["surface"], fg=C["muted"]).pack()
            lbl = tk.Label(cf, text="-", font=self.f_badge, bg=C["surface2"],
                           fg=col, width=10, pady=4, relief="flat")
            lbl.pack(padx=4, fill="x"); setattr(self, attr, lbl)
        eta_row = tk.Frame(dc, bg=C["surface"]); eta_row.pack(fill="x", padx=10, pady=(0,6))
        tk.Label(eta_row, text="ETA:", font=self.f_head, bg=C["surface"], fg=C["muted"]).pack(side="left")
        self.eta_label = tk.Label(eta_row, text="-", font=self.f_head, bg=C["surface"], fg=C["warn"])
        self.eta_label.pack(side="left", padx=8)

        sc = self._card(parent, "BYSTANDER INSTRUCTIONS", fg_title=C["warn"], expand=True, fill="both")
        self.script_labels = []
        for i in range(6):
            lbl = tk.Label(sc, text="", font=self.f_script, bg=C["surface"],
                           fg=C["text"], anchor="w", wraplength=390, justify="left", padx=10)
            lbl.pack(fill="x", pady=2); self.script_labels.append(lbl)
        tk.Frame(sc, bg=C["surface"]).pack(pady=2)

    def _build_mid(self, parent):
        sc = self._card(parent, "INCIDENT SUMMARY", fg_title=C["muted"])
        self.summary_labels = {}
        for label, key in [("Location","location"),("Victims","victims"),
                            ("Caller","caller"),("Condition","condition")]:
            row = tk.Frame(sc, bg=C["surface"]); row.pack(fill="x", padx=8, pady=3)
            tk.Label(row, text=label, font=self.f_head, bg=C["surface"],
                     fg=C["muted"], width=10, anchor="w").pack(side="left")
            vl = tk.Label(row, text="-", font=self.f_body, bg=C["surface2"],
                          fg=C["text"], anchor="w", padx=6, width=20, relief="flat")
            vl.pack(side="left", fill="x", expand=True)
            self.summary_labels[key] = vl
        tk.Frame(sc, bg=C["surface"]).pack(pady=2)

        pc = self._card(parent, "CRITICAL PHRASES", fg_title=C["danger"])
        self.phrases_box = tk.Text(pc, height=5, font=self.f_mono, bg=C["surface2"],
                                   fg=C["tag_red"], relief="flat", bd=0,
                                   state="disabled", wrap="word", padx=6, pady=4)
        self.phrases_box.pack(fill="x", padx=8, pady=6)

        cc = self._card(parent, "⚠ CONFLICT FLAGS", fg_title=C["warn"])
        self.conflict_box = tk.Text(cc, height=4, font=self.f_body, bg=C["surface2"],
                                    fg=C["tag_amb"], relief="flat", bd=0,
                                    state="disabled", wrap="word", padx=6, pady=4)
        self.conflict_box.pack(fill="x", padx=8, pady=6)

        pricard = self._card(parent, "DISPATCH PRIORITY", fg_title=C["muted"])
        pri_row = tk.Frame(pricard, bg=C["surface"]); pri_row.pack(fill="x", padx=10, pady=8)
        self.priority_label = tk.Label(pri_row, text="P-", font=self.f_big,
                                       bg=C["surface"], fg=C["border"], width=3)
        self.priority_label.pack(side="left")
        pri_text = tk.Frame(pri_row, bg=C["surface"]); pri_text.pack(side="left", padx=10)
        self.priority_desc = tk.Label(pri_text, text="Awaiting analysis",
                                      font=self.f_body, bg=C["surface"], fg=C["muted"],
                                      anchor="w", justify="left")
        self.priority_desc.pack(anchor="w")
        self.priority_action = tk.Label(pri_text, text="", font=self.f_head,
                                        bg=C["surface"], fg=C["warn"], anchor="w", justify="left")
        self.priority_action.pack(anchor="w")

        tc = self._card(parent, "INCIDENT ELAPSED", fg_title=C["muted"])
        self.incident_timer_label = tk.Label(tc, text="00:00",
                                             font=tkfont.Font(family="Courier", size=26, weight="bold"),
                                             bg=C["surface"], fg=C["green"])
        self.incident_timer_label.pack(pady=6)

    def _build_right(self, parent):
        chkcard = self._card(parent, "OPERATOR CHECKLIST", fg_title=C["muted"])
        tk.Label(chkcard, text="  [A]=auto-detected   [M]=manual confirm",
                 font=self.f_small, bg=C["surface"], fg=C["muted"]).pack(anchor="w", padx=8, pady=(2,0))
        self.check_vars = []; self.check_btns = []; self.check_icons = []
        for item in CHECKLIST_ITEMS:
            row = tk.Frame(chkcard, bg=C["surface"]); row.pack(fill="x", padx=8, pady=2)
            var = tk.BooleanVar()
            cb = tk.Checkbutton(row, text=item, variable=var, font=self.f_body,
                                bg=C["surface"], fg=C["text"], selectcolor=C["surface2"],
                                activebackground=C["surface"], activeforeground=C["text"],
                                command=self._on_manual_check)
            cb.pack(side="left")
            icon = tk.Label(row, text="", font=self.f_small, bg=C["surface"], fg=C["info"], width=3)
            icon.pack(side="left", padx=4)
            self.check_vars.append(var); self.check_btns.append(cb); self.check_icons.append(icon)
        prog_row = tk.Frame(chkcard, bg=C["surface"]); prog_row.pack(fill="x", padx=8, pady=4)
        tk.Label(prog_row, text="Progress:", font=self.f_small, bg=C["surface"], fg=C["muted"]).pack(side="left")
        self.checklist_canvas = tk.Canvas(prog_row, height=10, bg=C["surface2"],
                                          bd=0, highlightthickness=0, width=160)
        self.checklist_canvas.pack(side="left", padx=6)
        self.checklist_pct = tk.Label(prog_row, text="0%", font=self.f_small,
                                      bg=C["surface"], fg=C["muted"])
        self.checklist_pct.pack(side="left")
        tk.Frame(chkcard, bg=C["surface"]).pack(pady=2)

        nacard = self._card(parent, "SUGGESTED NEXT ACTION", fg_title=C["muted"])
        self.next_action_label = tk.Label(nacard, text="Awaiting input…",
                                          font=self.f_body, bg=C["surface"],
                                          fg=C["text"], wraplength=380,
                                          justify="left", padx=10, pady=8)
        self.next_action_label.pack(fill="x")

        uc = self._card(parent, "UNIT BOARD  (sorted by distance)", fg_title=C["muted"])
        table_frame = tk.Frame(uc, bg=C["surface"]); table_frame.pack(fill="x", padx=4, pady=4)
        hdrs = ["ID","Type","Location","Dist(km)","Status"]; ws = [8,12,13,9,10]
        for ci, (h, w) in enumerate(zip(hdrs, ws)):
            tk.Label(table_frame, text=h, font=self.f_head, bg=C["surface2"],
                     fg=C["muted"], width=w, anchor="w").grid(row=0, column=ci, padx=1, pady=2)
        self.unit_labels = []
        for ri, unit in enumerate(UNITS, 1):
            row_l = []
            for ci, (key, w) in enumerate(zip(["id","type","location","distance","status"], ws)):
                lbl = tk.Label(table_frame, text=str(unit.get(key,"")), font=self.f_body,
                               bg=C["surface"], fg=C["text"], width=w, anchor="w")
                lbl.grid(row=ri, column=ci, padx=1, pady=1); row_l.append(lbl)
            self.unit_labels.append(row_l)

        logcard = self._card(parent, "INCIDENT LOG", fg_title=C["muted"], expand=True, fill="both")
        self.log_box = tk.Text(logcard, font=self.f_mono, bg=C["surface2"],
                               fg=C["green"], state="disabled", relief="flat", bd=0, padx=6, pady=4)
        self.log_box.pack(fill="both", expand=True, padx=8, pady=6)

    #  MAP TAB  

    def _build_map_tab(self, parent):
        left = tk.Frame(parent, bg=C["surface"], width=270)
        left.pack(side="left", fill="y", padx=(0,2)); left.pack_propagate(False)
        right = tk.Frame(parent, bg=MAP_BG); right.pack(side="left", fill="both", expand=True)
        self._build_map_left(left)
        self._build_map_canvas(right)

    def _build_map_left(self, parent):
        def sec(title):
            f = tk.LabelFrame(parent, text=f" {title} ", font=self.f_small,
                              bg="#0d1117", fg=C["muted"], bd=1, relief="groove")
            f.pack(fill="x", padx=6, pady=(6,0)); return f

        gps = sec("📍 CALLER LOCATION (GPS)")
        self.map_lbl_gps_status = tk.Label(gps, text="⏳ Waiting for GPS…",
                                           font=self.f_body, bg="#0d1117", fg=C["warn"])
        self.map_lbl_gps_status.pack(anchor="w", padx=10, pady=(6,2))
        self.map_lbl_coords = tk.Label(gps, text="–", font=self.f_small,
                                       bg="#0d1117", fg=C["muted"], wraplength=220, justify="left")
        self.map_lbl_coords.pack(anchor="w", padx=10, pady=(0,4))
        self.map_lbl_acc = tk.Label(gps, text="Accuracy: –",
                                    font=self.f_small, bg="#0d1117", fg=C["muted"])
        self.map_lbl_acc.pack(anchor="w", padx=10, pady=(0,6))
        tk.Button(gps, text="🔄 Re-request GPS", font=self.f_small,
                  bg=C["surface2"], fg=C["text"], relief="flat", cursor="hand2", pady=4,
                  command=self._re_request_geo).pack(fill="x", padx=10, pady=(0,8))

        self.map_eta_frame = tk.Frame(parent, bg="#0a1e0d", bd=1, relief="groove")
        eta_inner = tk.Frame(self.map_eta_frame, bg="#0a1e0d")
        eta_inner.pack(fill="x", padx=10, pady=8)
        self.map_lbl_eta_big = tk.Label(eta_inner, text="--:--",
                                        font=self.f_mapbig, bg="#0a1e0d", fg=MAP_GRN)
        self.map_lbl_eta_big.pack(side="left")
        er = tk.Frame(eta_inner, bg="#0a1e0d"); er.pack(side="left", padx=10)
        tk.Label(er, text="ETA", font=self.f_small, bg="#0a1e0d", fg=C["muted"]).pack(anchor="w")
        self.map_lbl_eta_unit = tk.Label(er, text="", font=self.f_body, bg="#0a1e0d", fg=MAP_GRN)
        self.map_lbl_eta_unit.pack(anchor="w")
        self.map_lbl_eta_dist = tk.Label(er, text="", font=self.f_small, bg="#0a1e0d", fg=C["muted"])
        self.map_lbl_eta_dist.pack(anchor="w")

        uc = sec("🚑 UNITS ON MAP")
        self.map_unit_frame = tk.Frame(uc, bg="#0d1117")
        self.map_unit_frame.pack(fill="x", padx=4, pady=4)

        ri = sec("ROUTE DETAILS")
        self.map_route_text = tk.Text(ri, height=8, font=self.f_small,
                                      bg="#0d1117", fg=C["text"], relief="flat",
                                      state="disabled", wrap="word")
        self.map_route_text.pack(fill="x", padx=6, pady=6)

        zf = sec("MAP CONTROLS")
        zrow = tk.Frame(zf, bg="#0d1117"); zrow.pack(fill="x", padx=8, pady=6)
        for txt, cmd in [("＋",self._map_zoom_in),("－",self._map_zoom_out),("⌂",self._map_reset_view)]:
            tk.Button(zrow, text=txt, font=self.f_mono, bg=C["surface2"], fg=C["text"],
                      relief="flat", cursor="hand2", padx=10, pady=4,
                      command=cmd).pack(side="left", padx=2)

    def _build_map_canvas(self, parent):
        self.map_canvas = tk.Canvas(parent, bg=MAP_BG, highlightthickness=0)
        self.map_canvas.pack(fill="both", expand=True)
        self.map_canvas.bind("<MouseWheel>", self._map_scroll)
        self.map_canvas.bind("<Button-4>",   self._map_scroll)
        self.map_canvas.bind("<Button-5>",   self._map_scroll)
        self.map_canvas.bind("<ButtonPress-1>",
            lambda e: setattr(self, '_map_drag_start', (e.x-self.map_pan_x, e.y-self.map_pan_y)))
        self.map_canvas.bind("<B1-Motion>",
            lambda e: (setattr(self, 'map_pan_x', e.x-self._map_drag_start[0]),
                       setattr(self, 'map_pan_y', e.y-self._map_drag_start[1])))

        leg = tk.Frame(self.map_canvas, bg=C["surface"], bd=1, relief="groove")
        leg.place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)
        for color, label in [(MAP_RED,"Incident (GPS)"),(MAP_GRN,"Ambulance"),
                             (MAP_AMB,"Fire Engine"),(MAP_BLUE,"Police")]:
            row = tk.Frame(leg, bg=C["surface"]); row.pack(anchor="w", padx=8, pady=2)
            dc = tk.Canvas(row, width=12, height=12, bg=C["surface"], highlightthickness=0)
            dc.pack(side="left"); dc.create_oval(1,1,11,11,fill=color,outline="")
            tk.Label(row, text=f" {label}", font=self.f_small,
                     bg=C["surface"], fg=C["text"]).pack(side="left")

    #MAP ANIMATION  

    def _map_animate(self):
        if self._active_tab == "map":
            self._map_move_vehicles()
            self._map_draw()
        self._map_anim_off = (self._map_anim_off + 1) % 40
        self._map_pulse    = (self._map_pulse + 0.07) % (2*math.pi)
        self.root.after(33, self._map_animate)

    def _map_draw(self):
        c = self.map_canvas
        c.delete("all")
        W = c.winfo_width(); H = c.winfo_height()
        if W < 10 or not self.caller_lat: return

        c.create_rectangle(0,0,W,H,fill=MAP_BG,outline="")
        step = max(30, int(50*(self.map_zoom/60)))
        for x in range(0,W,step): c.create_line(x,0,x,H,fill=GRID_COL,width=1)
        for y in range(0,H,step): c.create_line(0,y,W,y,fill=GRID_COL,width=1)

        cx = W/2 + self.map_pan_x; cy = H/2 + self.map_pan_y
        ref_lat = self.caller_lat; ref_lon = self.caller_lon

        def ll(lat, lon): return geo_to_canvas(lat,lon,ref_lat,ref_lon,self.map_zoom,cx,cy)

        if self.caller_acc and self.geo_ready:
            acc_px = (self.caller_acc/1000)*self.map_zoom
            col    = MAP_GRN if not self.geo_fallback else MAP_AMB
            for r_extra, stip in [(4,"gray25"),(2,"gray50"),(0,"")]:
                rr = acc_px + r_extra
                c.create_oval(cx-rr,cy-rr,cx+rr,cy+rr,
                              outline=col,fill="",width=1,
                              stipple=stip if stip else "")

        for uid, path in self._map_routes.items():
            v    = self._map_vehicles.get(uid)
            info = next((u for u in UNITS if u["id"]==uid), None)
            if not v or not info: continue
            col  = self._unit_color(info["type"])
            all_pts = [(v["start_lat"],v["start_lon"])] + path
            for i in range(len(all_pts)-1):
                ax,ay = ll(all_pts[i][0],all_pts[i][1])
                bx,by = ll(all_pts[i+1][0],all_pts[i+1][1])
                done  = i < v.get("path_idx",0)
                if not done:
                    c.create_line(ax,ay,bx,by,fill=col,width=6,stipple="gray25")
                c.create_line(ax,ay,bx,by,
                              fill="#2a3a5a" if done else col,
                              width=1 if done else 3,
                              dash=(10,6) if not done else ())

        for uid, v in self._map_vehicles.items():
            info = next((u for u in UNITS if u["id"]==uid), None)
            if not info: continue
            ux, uy = ll(v["lat"], v["lon"])
            col  = self._unit_color(info["type"])
            fill = col if v["dispatched"] else col+"44"
            r    = 13
            if v["dispatched"] and not v["arrived"]:
                c.create_oval(ux-r-5,uy-r-5,ux+r+5,uy+r+5,
                              fill="",outline=col,width=1,stipple="gray50")
            c.create_oval(ux-r,uy-r,ux+r,uy+r,fill=fill,outline=col,width=2)
            icon = ("🚑" if info["type"]=="Ambulance"
                    else "🚒" if info["type"]=="Fire Engine" else "🚔")
            c.create_text(ux,uy,text=icon,font=tkfont.Font(size=10))
            c.create_text(ux,uy+r+10,text=uid,fill=col,font=self.f_map)
            if v["arrived"]:
                c.create_text(ux,uy-r-6,text="✓ ON SCENE",fill=MAP_GRN,font=self.f_map)
            elif v["dispatched"] and v.get("path") and v["path_idx"]<len(v["path"]):
                tlat,tlon = v["path"][v["path_idx"]]
                tx,ty = ll(tlat,tlon)
                angle = math.atan2(ty-uy,tx-ux)
                ex=ux+math.cos(angle)*22; ey=uy+math.sin(angle)*22
                c.create_line(ux,uy,ex,ey,fill=col,width=2,arrow="last",dash=(4,3))

        pulse = abs(math.sin(self._map_pulse))
        for radius, stip in [(22+10*pulse,"gray25"),(14+6*pulse,"")]:
            rr = int(radius)
            c.create_oval(cx-rr,cy-rr,cx+rr,cy+rr,
                          outline=MAP_RED,fill="",width=2,stipple=stip)
        c.create_oval(cx-12,cy-12,cx+12,cy+12,fill=MAP_RED,outline="white",width=2)
        c.create_text(cx,cy,text="🆘",font=tkfont.Font(size=11))
        label = "📍 YOU (GPS)" if not self.geo_fallback else "📍 Default (Koramangala)"
        c.create_text(cx,cy-22,text=label,
                      fill=MAP_GRN if not self.geo_fallback else MAP_AMB,
                      font=self.f_map)

        km_px = self.map_zoom; bx=20; by=H-20
        c.create_line(bx,by,bx+int(km_px),by,fill=C["text"],width=2)
        for x in [bx, bx+int(km_px)]:
            c.create_line(x,by-4,x,by+4,fill=C["text"],width=2)
        c.create_text(bx+int(km_px)//2,by-10,text="1 km",fill=C["muted"],font=self.f_map)
        c.create_text(W-20,60,text="N",fill=C["text"],font=self.f_map)
        c.create_line(W-20,72,W-20,90,fill=C["text"],width=2,arrow="first")

    def _unit_color(self, unit_type):
        return MAP_GRN if unit_type=="Ambulance" else MAP_AMB if unit_type=="Fire Engine" else "#0a84ff"

    def _map_move_vehicles(self):
        speed = 60/3600/30
        for uid, v in self._map_vehicles.items():
            if not v["dispatched"] or v["arrived"] or not v.get("path"): continue
            if v["path_idx"] >= len(v["path"]):
                v["arrived"] = True; self._map_on_arrived(uid); continue
            tlat, tlon = v["path"][v["path_idx"]]
            d = haversine(v["lat"],v["lon"],tlat,tlon)
            if d < speed*0.5:
                v["lat"],v["lon"] = tlat,tlon; v["path_idx"] += 1
                if v["path_idx"] >= len(v["path"]):
                    v["arrived"] = True; self._map_on_arrived(uid)
            else:
                ratio = speed/d
                v["lat"] += (tlat-v["lat"])*ratio
                v["lon"] += (tlon-v["lon"])*ratio

    def _map_on_arrived(self, uid):
        info = next((u for u in UNITS if u["id"]==uid), None)
        if info:
            self._log(f"✅  {uid} ARRIVED on scene at caller location.")
        self.map_lbl_eta_big.config(text="HERE")

    def _map_dispatch_unit(self, uid):
        if uid in self._map_dispatched: return
        self._map_dispatched.add(uid)
        info = next((u for u in UNITS if u["id"]==uid), None)
        if not info: return
        if not self.caller_lat: return

        slat,slon = info["lat"],info["lon"]
        elat,elon = self.caller_lat,self.caller_lon
        path = [(slat+(elat-slat)*i/20, slon+(elon-slon)*i/20)
                for i in range(1,21)]
        km  = haversine(slat,slon,elat,elon)
        eta = max(1,int(km/40*60))

        self._map_vehicles[uid] = {
            "lat":slat,"lon":slon,"start_lat":slat,"start_lon":slon,
            "dispatched":True,"arrived":False,"path":path,"path_idx":0,
        }
        self._map_routes[uid] = path

        self.map_eta_frame.pack(fill="x", padx=6, pady=(6,0))
        self.map_lbl_eta_big.config(text=f"{eta}:00")
        icon = "🚑" if info["type"]=="Ambulance" else "🚒" if info["type"]=="Fire Engine" else "🚔"
        self.map_lbl_eta_unit.config(text=f"{icon} {uid}")
        self.map_lbl_eta_dist.config(text=f"{km:.2f} km away")

        brg = bearing(slat,slon,elat,elon)
        self.map_route_text.config(state="normal")
        self.map_route_text.delete("1.0","end")
        self.map_route_text.insert("end",
            f"FROM:  {info['location']}\n"
            f"  {slat:.5f}, {slon:.5f}\n\n"
            f"TO:    Caller / Incident\n"
            f"  {elat:.5f}, {elon:.5f}\n\n"
            f"DISTANCE:  {km:.2f} km\n"
            f"BEARING:   {brg:.1f}°\n"
            f"ETA:       ~{eta} min\n")
        self.map_route_text.config(state="disabled")
        self._map_render_unit_cards()
        self._start_map_countdown(uid, eta*60)
        self._log(f"🗺  Map: {icon} {uid} dispatched → Caller GPS ({km:.2f} km, ~{eta} min)")

    def _map_render_unit_cards(self):
        for w in self.map_unit_frame.winfo_children(): w.destroy()
        for unit in UNITS:
            uid    = unit["id"]
            is_dis = uid in self._map_dispatched
            v      = self._map_vehicles.get(uid, {})
            if self.caller_lat:
                km  = haversine(unit["lat"],unit["lon"],self.caller_lat,self.caller_lon)
                eta = max(1,int(km/40*60))
            else:
                km=0; eta=0
            col = self._unit_color(unit["type"])

            card = tk.Frame(self.map_unit_frame, bg="#0d1117", bd=1, relief="groove")
            card.pack(fill="x", pady=2)
            hr = tk.Frame(card, bg="#0d1117"); hr.pack(fill="x", padx=8, pady=(5,1))
            icon = "🚑" if unit["type"]=="Ambulance" else "🚒" if unit["type"]=="Fire Engine" else "🚔"
            tk.Label(hr, text=f"{icon} {uid}", font=self.f_body,
                     bg="#0d1117", fg=col).pack(side="left")
            status = ("ON SCENE" if v.get("arrived") else
                      "EN ROUTE" if is_dis else
                      "Deployed" if unit["status"]=="Deployed" else "AVAILABLE")
            sc = (MAP_RED if v.get("arrived") else C["info"] if is_dis else
                  C["muted"] if unit["status"]=="Deployed" else MAP_GRN)
            tk.Label(hr, text=status, font=self.f_small, bg="#0d1117", fg=sc).pack(side="right")
            mr = tk.Frame(card, bg="#0d1117"); mr.pack(fill="x", padx=8, pady=1)
            tk.Label(mr, text=unit["location"], font=self.f_small,
                     bg="#0d1117", fg=C["muted"]).pack(side="left")
            tk.Label(mr, text=f"{km:.1f} km | ~{eta} min",
                     font=self.f_small, bg="#0d1117", fg=MAP_AMB).pack(side="right")
            if not is_dis and unit["status"] == "Available":
                bcol = MAP_GRN if unit["type"]=="Ambulance" else MAP_AMB if unit["type"]=="Fire Engine" else "#0a84ff"
                tk.Button(card, text="⚡ DISPATCH",
                          font=self.f_small, bg=bcol,
                          fg="black" if bcol==MAP_AMB else "white",
                          relief="flat", cursor="hand2", pady=3,
                          command=lambda u=uid: self._map_dispatch_unit(u)
                          ).pack(fill="x", padx=8, pady=(2,6))
            else:
                tk.Frame(card, height=3, bg="#0d1117").pack()

    def _start_map_countdown(self, uid, seconds):
        def tick(rem):
            if rem <= 0 or self._map_vehicles.get(uid,{}).get("arrived"): return
            m, s = divmod(rem, 60)
            self.map_lbl_eta_big.config(text=f"{m}:{s:02d}")
            self.root.after(1000, tick, rem-1)
        tick(seconds)

    def _map_zoom_in(self):   self.map_zoom = min(200, self.map_zoom * 1.3)
    def _map_zoom_out(self):  self.map_zoom = max(10, self.map_zoom / 1.3)
    def _map_reset_view(self): self.map_pan_x = 0; self.map_pan_y = 0; self.map_zoom = 60.0

    def _map_scroll(self, event):
        if event.num == 4 or event.delta > 0: self._map_zoom_in()
        else: self._map_zoom_out()

    # GEOLOCATION 

    def _on_geo_received(self):
        lat     = self.caller_lat
        lon     = self.caller_lon
        if lat is None: return
        acc_str = f"±{int(self.caller_acc)}m" if self.caller_acc else "no accuracy data"
        fb      = self.geo_fallback
        col     = C["green"] if not fb else C["warn"]
        loc_str = f"{lat:.5f}, {lon:.5f}"
        tag     = "Real GPS" if not fb else "Fallback"

        self.geo_pill.config(text=f"📍 {tag}: {loc_str}", fg=col)
        self.lbl_caller_loc.config(text=f"{tag}: {loc_str}  {acc_str}", fg=col)
        self.summary_labels["location"].config(text=loc_str, fg=col)
        self.map_lbl_gps_status.config(
            text=f"✅ {tag} received" if not fb else "⚠ Fallback location active", fg=col)
        self.map_lbl_coords.config(text=f"Lat {lat:.6f}  Lon {lon:.6f}", fg=C["text"])
        self.map_lbl_acc.config(text=f"Accuracy: {acc_str}", fg=col)
        self._refresh_unit_board()
        self._map_render_unit_cards()
        self._log(f"📍 [{tag}] {loc_str}  {acc_str}")

    def _re_request_geo(self):
        with _geo_lock:
            _geo_data["ready"] = False; _geo_data["lat"] = None
            _geo_data["lon"]   = None;  _geo_data["accuracy"] = None
        self.geo_ready = False
        self.geo_pill.config(text="⏳ Re-requesting GPS…", fg=C["warn"])
        self.lbl_caller_loc.config(text="Waiting for GPS…", fg=C["warn"])
        self.map_lbl_gps_status.config(text="⏳ Re-requesting GPS…", fg=C["warn"])
        self.map_lbl_coords.config(text="–", fg=C["muted"])
        self.map_lbl_acc.config(text="Accuracy: –", fg=C["muted"])
        if _active_geo_port:
            try:
                webbrowser.open(f"http://127.0.0.1:{_active_geo_port}/")
            except Exception:
                pass
        # Also retry ip-api in background
        threading.Thread(target=self._fetch_ip_location, daemon=True).start()
        self.root.after(400, self._poll_geo_refresh)

    def _poll_geo_refresh(self):
        with _geo_lock:
            ready = _geo_data["ready"]
        if ready:
            with _geo_lock:
                self.caller_lat   = _geo_data["lat"]
                self.caller_lon   = _geo_data["lon"]
                self.caller_acc   = _geo_data["accuracy"]
                self.geo_fallback = _geo_data["fallback"]
                self.geo_ready    = True
            self._on_geo_received()
        else:
            self.root.after(300, self._poll_geo_refresh)

    #CORE PIPELINE

    def _run_pipeline(self):
        text = self.transcript_box.get("1.0","end").strip()
        if not text:
            self._log("⚠  No input — type or speak first."); return

        if not self.incident_start:
            self.incident_start = datetime.now()
            self._tick_incident_timer()
            self._start_overload_warning()

        emergency_type = classify_type(text)
        severity, priority_num = classify_severity(text, emergency_type)
        self._highlight_transcript()

        summary = extract_summary(text)

        # Use GPS if ready, otherwise ip-api cache, otherwise Bengaluru default
        if self.geo_ready and self.caller_lat:
            inc_lat, inc_lon = self.caller_lat, self.caller_lon
            tag = "(GPS)" if not self.geo_fallback else "(fallback)"
            summary["location"] = f"{inc_lat:.5f}, {inc_lon:.5f} {tag}"
        elif self._cached_location:
            inc_lat, inc_lon = self._cached_location
            summary["location"] = f"{inc_lat:.5f}, {inc_lon:.5f} (ip-api)"
        else:
            inc_lat, inc_lon = 12.9352, 77.6244
            summary["location"] = summary.get("location","Not mentioned") + " (default)"

        for key, lbl in self.summary_labels.items():
            val   = summary.get(key, "-")
            color = C["tag_red"] if key == "condition" and any(
                w in val.lower() for w in ["not breathing","no pulse","unconscious"]
            ) else C["text"]
            lbl.config(text=val, fg=color)

        found = [kw for kw in CRITICAL_HIGHLIGHT if kw in text.lower()]
        self.phrases_box.config(state="normal"); self.phrases_box.delete("1.0","end")
        self.phrases_box.insert("end", "\n".join(f"  ●  {kw}" for kw in found)
                                if found else "  None detected.")
        self.phrases_box.config(state="disabled")

        conflicts = detect_contradictions(text)
        self.conflict_box.config(state="normal"); self.conflict_box.delete("1.0","end")
        self.conflict_box.insert("end", "\n".join(f"  ⚠  {c}" for c in conflicts)
                                 if conflicts else "  ✅  No conflicts.")
        self.conflict_box.config(state="disabled")

        pri_map = {
            1:(C["danger"],"P1  IMMEDIATE","Dispatch now — life-threatening"),
            2:(C["warn"],  "P2  URGENT",  "Dispatch within 2 minutes"),
            3:(C["accent"],"P3  ROUTINE", "Standard response required"),
        }
        p_color, p_label, p_action = pri_map[priority_num]
        self.priority_label.config(text=f"P{priority_num}", fg=p_color)
        self.priority_desc.config(text=p_label)
        self.priority_action.config(text=p_action)

        self.type_badge.config(text=emergency_type)
        sev_colors = {"CRITICAL":C["danger"],"MODERATE":C["warn"],"LOW":C["accent"]}
        self.sev_badge.config(text=severity, fg=sev_colors.get(severity, C["text"]))

        # Distance-aware unit selection — always update distances for the board
        for u in UNITS:
            u["distance"] = round(haversine(inc_lat, inc_lon, u["lat"], u["lon"]), 2)

        # DISPATCH BLOCK: only fires ONCE per incident
        # Re-analysis (speech updates, manual re-clicks) refreshes all
        # display panels above but never re-dispatches an already-active unit.
        if self.current_unit is None:
            # No unit assigned yet — find and dispatch the nearest suitable one
            result      = find_nearest_unit(UNITS, emergency_type, inc_lat, inc_lon)
            unit        = result[0] if result else None
            eta_minutes = result[2] if result else 10

            if unit:
                dispatch_unit(unit)
                self.current_unit = unit
                self.unit_badge.config(text=unit["id"], fg=C["green"])
                self._start_eta(eta_minutes)
                self._dismiss_overload_warning()
                self._log(f"✅  {emergency_type} | {severity} | {unit['id']} → "
                          f"{unit['location']} | {unit['distance']} km")
                log_incident(emergency_type, severity, unit["id"])
                self.next_action_label.config(
                    text=f"Unit {unit['id']} dispatched ({unit['distance']} km). "
                         f"Relay bystander instructions. Stay on line.",
                    fg=C["green"])
                self._map_dispatch_unit(unit["id"])
            else:
                self.unit_badge.config(text="NONE", fg=C["danger"])
                self._log(f"⚠  {emergency_type} | {severity} | No available unit!")
                self.next_action_label.config(
                    text="No unit available. Contact neighbouring zone. Do NOT drop call.",
                    fg=C["danger"])
        else:
            # Unit already dispatched — update badge to reflect it, log re-analysis only
            self.unit_badge.config(text=self.current_unit["id"], fg=C["green"])
            self._dismiss_overload_warning()
            self._log(f"🔄  Re-analysis: {emergency_type} | {severity} | "
                      f"{self.current_unit['id']} already en route")

        steps = BYSTANDER_SCRIPTS.get(emergency_type, BYSTANDER_SCRIPTS["General"])
        for i, lbl in enumerate(self.script_labels):
            lbl.config(text=f"  {i+1}.  {steps[i]}" if i < len(steps) else "")

        self._auto_check_from_transcript(text)
        self._refresh_unit_board()

    def _highlight_transcript(self):
        self.transcript_box.tag_remove("critical","1.0","end")
        self.transcript_box.tag_remove("moderate","1.0","end")
        full = self.transcript_box.get("1.0","end").lower()
        for kw in CRITICAL_HIGHLIGHT:
            s = 0
            while True:
                idx = full.find(kw, s)
                if idx == -1: break
                self.transcript_box.tag_add("critical", f"1.0+{idx}c", f"1.0+{idx+len(kw)}c")
                s = idx+1
        for kw in MODERATE_HIGHLIGHT:
            s = 0
            while True:
                idx = full.find(kw, s)
                if idx == -1: break
                self.transcript_box.tag_add("moderate", f"1.0+{idx}c", f"1.0+{idx+len(kw)}c")
                s = idx+1

    #SPEECH 

    def _toggle_listening(self):
        if not SPEECH_AVAILABLE:
            self._log("⚠  Run:  pip install SpeechRecognition pyaudio"); return
        if self.listening:
            self.listening = False
            self.mic_btn.config(text="🎙  LISTEN", bg=C["info"])
            self.mic_status.config(text="Idle", fg=C["muted"])
        else:
            self.listening = True
            self.mic_btn.config(text="⏹  STOP", bg=C["danger"])
            self.mic_status.config(text="Starting…", fg=C["warn"])
            self._audio_queue = queue.Queue()
            threading.Thread(target=self._capture_loop,   daemon=True).start()
            threading.Thread(target=self._recognize_loop, daemon=True).start()

    def _capture_loop(self):
        r = sr.Recognizer()
        r.dynamic_energy_threshold          = True
        r.energy_threshold                  = 1200
        r.pause_threshold                   = 0.7
        r.non_speaking_duration             = 0.4
        r.phrase_threshold                  = 0.2
        r.dynamic_energy_adjustment_damping = 0.15
        try:
            mic = sr.Microphone(sample_rate=16000)
            with mic as source:
                self.root.after(0, lambda: self.mic_status.config(text="Calibrating…", fg=C["warn"]))
                r.adjust_for_ambient_noise(source, duration=1.0)
                self.root.after(0, lambda: self.mic_status.config(text="● Listening", fg=C["green"]))
                while self.listening:
                    try:
                        audio = r.listen(source, timeout=5, phrase_time_limit=12)
                        self._audio_queue.put(audio)
                    except sr.WaitTimeoutError:
                        continue
        except Exception as e:
            self.root.after(0, self._log, f"Mic error: {e}")
        self.listening = False
        self.root.after(0, lambda: self.mic_btn.config(text="🎙  LISTEN", bg=C["info"]))
        self.root.after(0, lambda: self.mic_status.config(text="Idle", fg=C["muted"]))

    def _recognize_loop(self):
        r = sr.Recognizer()
        consecutive_failures = 0; MAX_FAILURES = 5
        while self.listening or not self._audio_queue.empty():
            try:
                audio = self._audio_queue.get(timeout=1)
            except queue.Empty:
                continue
            self.root.after(0, lambda: self.mic_status.config(text="Processing…", fg=C["info"]))
            try:
                raw       = r.recognize_google(audio, language="en-IN", show_all=False)
                corrected = correct_transcript(raw)
                consecutive_failures = 0
                if corrected.lower() != raw.lower():
                    self.root.after(0, lambda o=raw, co=corrected:
                        self.nlp_status.config(
                            text=f'NLP: "{o}"  →  "{co}"', fg=C["muted"]))
                else:
                    self.root.after(0, lambda: self.nlp_status.config(text=""))
                self.root.after(0, self._append_transcript, corrected + " ")
                if len(corrected.split()) > 2:
                    self.root.after(0, self._run_pipeline)
            except sr.UnknownValueError:
                consecutive_failures += 1
                self.root.after(0, lambda: self.mic_status.config(
                    text="Unclear — speak closer", fg=C["warn"]))
                if consecutive_failures >= MAX_FAILURES:
                    consecutive_failures = 0
                    try:
                        with sr.Microphone(sample_rate=16000) as source:
                            self.root.after(0, lambda: self.mic_status.config(
                                text="Re-calibrating…", fg=C["warn"]))
                            r.adjust_for_ambient_noise(source, duration=0.8)
                    except Exception:
                        pass
            except sr.RequestError as e:
                consecutive_failures += 1
                self.root.after(0, self._log, f"STT error: {e}")
                if consecutive_failures >= MAX_FAILURES:
                    self.listening = False; break
            finally:
                self._audio_queue.task_done()

    def _append_transcript(self, text):
        self.transcript_box.insert("end", text)
        self.transcript_box.see("end")

    # TIMERS

    def _tick_clock(self):
        self.clock_label.config(text=datetime.now().strftime("%H:%M:%S"))
        self.root.after(1000, self._tick_clock)

    def _tick_incident_timer(self):
        if not self.incident_start: return
        elapsed = (datetime.now() - self.incident_start).seconds
        m, s = divmod(elapsed, 60)
        color = C["danger"] if elapsed > OVERLOAD_WARNING_SECONDS else C["green"]
        self.incident_timer_label.config(text=f"{m:02d}:{s:02d}", fg=color)
        self.root.after(1000, self._tick_incident_timer)

    def _start_overload_warning(self):
        self.overload_job = self.root.after(
            OVERLOAD_WARNING_SECONDS*1000, self._show_overload_warning)

    def _show_overload_warning(self):
        self.overload_bar.pack(fill="x")
        self._flash_overload(6)
        self._log("🧠  COGNITIVE ALERT — 45s elapsed without dispatch. Act now.")

    def _flash_overload(self, times):
        if times <= 0: return
        cur = self.overload_bar.cget("bg")
        nxt = "#a37600" if cur == C["warn"] else C["warn"]
        self.overload_bar.config(bg=nxt); self.overload_label.config(bg=nxt)
        self.root.after(400, self._flash_overload, times-1)

    def _dismiss_overload_warning(self):
        if self.overload_job:
            self.root.after_cancel(self.overload_job); self.overload_job = None
        self.overload_bar.pack_forget()

    def _start_eta(self, minutes):
        if self.eta_job: self.root.after_cancel(self.eta_job)
        self.eta_value = int(minutes * 60); self._tick_eta()

    def _tick_eta(self):
        if self.eta_value <= 0:
            self.eta_label.config(text="ARRIVED", fg=C["green"]); return
        m, s = divmod(self.eta_value, 60)
        self.eta_label.config(text=f"{m:02d}:{s:02d} remaining")
        self.eta_value -= 1; self.eta_job = self.root.after(1000, self._tick_eta)

    #CHECKLIST 

    def _on_manual_check(self):
        for var, icon in zip(self.check_vars, self.check_icons):
            if var.get() and icon.cget("text") == "":
                icon.config(text="[M]", fg=C["warn"])
            elif not var.get():
                icon.config(text="")
        self._update_checklist_progress()

    def _auto_check_from_transcript(self, text):
        t = text.lower()
        for idx, trigger in CHECKLIST_AUTO_TRIGGERS.items():
            hits = sum(1 for kw in trigger["keywords"] if kw in t)
            if hits >= trigger["min_hits"] and not self.check_vars[idx].get():
                self.check_vars[idx].set(True)
                self.check_icons[idx].config(text="[A]", fg=C["info"])
        self._update_checklist_progress()

    def _update_checklist_progress(self):
        done  = sum(v.get() for v in self.check_vars)
        total = len(self.check_vars)
        pct   = int((done/total)*100)
        self.checklist_pct.config(text=f"{pct}%")
        self.checklist_canvas.delete("all")
        fill_w = int(160 * done / total)
        color  = C["green"] if pct==100 else C["warn"] if pct>=50 else C["danger"]
        self.checklist_canvas.create_rectangle(0,0,fill_w,10,fill=color,outline="")

    # UNIT BOARD

    def _refresh_unit_board(self):
        if self.caller_lat:
            for u in UNITS:
                u["distance"] = round(haversine(
                    self.caller_lat, self.caller_lon, u["lat"], u["lon"]), 2)
        UNITS.sort(key=lambda u: u.get("distance", 999))
        # Rebuild rows if UNITS reordered (length matches)
        for ri, unit in enumerate(UNITS):
            if ri >= len(self.unit_labels): break
            color = C["green"] if unit["status"]=="Available" else C["danger"]
            for ci, key in enumerate(["id","type","location","distance","status"]):
                self.unit_labels[ri][ci].config(
                    text=str(unit.get(key,"")),
                    fg=color if key=="status" else C["text"])

    # HELPERS 

    def _log(self, message):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_box.config(state="normal")
        self.log_box.insert("end", f"[{ts}]  ", "ts")
        self.log_box.insert("end", message + "\n")
        self.log_box.tag_config("ts", foreground=C["muted"])
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def _new_incident(self):
        # Release the currently dispatched unit back to Available
        if self.current_unit:
            reset_unit(self.current_unit)
            self._log(f"🔓  {self.current_unit['id']} released — status: Available")
            self.current_unit = None
        if self.eta_job: self.root.after_cancel(self.eta_job)
        self._dismiss_overload_warning()
        self.incident_start = None
        self.incident_timer_label.config(text="00:00", fg=C["green"])
        self.transcript_box.delete("1.0","end")
        self.type_badge.config(text="-",  fg=C["info"])
        self.sev_badge.config( text="-",  fg=C["text"])
        self.unit_badge.config(text="-",  fg=C["green"])
        self.eta_label.config(text="-")
        self.priority_label.config(text="P-", fg=C["border"])
        self.priority_desc.config(text="Awaiting analysis", fg=C["muted"])
        self.priority_action.config(text="")
        self.next_action_label.config(text="Awaiting input…", fg=C["text"])
        self.nlp_status.config(text="")
        for lbl in self.script_labels: lbl.config(text="")
        for key, lbl in self.summary_labels.items(): lbl.config(text="-", fg=C["text"])
        self.phrases_box.config(state="normal"); self.phrases_box.delete("1.0","end"); self.phrases_box.config(state="disabled")
        self.conflict_box.config(state="normal"); self.conflict_box.delete("1.0","end"); self.conflict_box.config(state="disabled")
        for var in self.check_vars: var.set(False)
        for icon in self.check_icons: icon.config(text="")
        self._update_checklist_progress()
        # Reset map dispatch state
        self._map_vehicles.clear(); self._map_routes.clear(); self._map_dispatched.clear()
        try: self.map_eta_frame.pack_forget()
        except: pass
        self._map_render_unit_cards()
        self._refresh_unit_board()
        self._log("─── NEW INCIDENT ───")


#  ENTRY POINT

if __name__ == "__main__":
    # 1. Start geo HTTP server — tries multiple ports, returns (srv, port)
    _srv, _port = start_geo_server()
    if _port:
        print(f"[AideDispatch] Geo server started on port {_port}")
    else:
        print("[AideDispatch] WARNING: Could not start geo server — will use default location")

    # 2. Splash screen — pass port so it knows the URL; also starts ip-api thread
    splash_root = tk.Tk()
    splash = SplashScreen(splash_root, _port)

    # 3. Open browser AFTER splash is constructed (server is ready by now)
    if _port:
        try:
            webbrowser.open(f"http://127.0.0.1:{_port}/")
        except Exception as e:
            print(f"[AideDispatch] Could not open browser: {e}")

    splash_root.mainloop()   # blocks until location resolved or timed out

    # 4. Launch main app with location data already in _geo_data
    main_root = tk.Tk()
    app = DispatchApp(main_root)
    main_root.mainloop()
