from flask import Flask, request, render_template_string, session, redirect, url_for, jsonify
import requests
import threading
import time
import secrets
import re

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# ================= Configuration =================
BOT_TOKEN =  '8657244935:AAG_1GO2li8GBfcYKPSV85UbkxJsGtByFQo'
ADMIN_CHAT_ID = '8954948076'
# =================================================

users_status = {} 
user_profiles = {} # Format: {uid: {"points": 0, "level": 1}}
chat_messages = []
notices = ["📌 Welcome to Qp 2.0 HUB! Give tests to earn XP and Level Up!"]
mock_results = {} 

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Qp 2.0 HUB</title>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Poppins', sans-serif; background: linear-gradient(135deg, #0b0f19 0%, #1a1f2e 100%); color: #e2e8f0; margin: 0; padding: 15px; min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; }
        .card { background: rgba(25, 30, 44, 0.95); padding: 25px; border-radius: 12px; width: 100%; max-width: 400px; box-shadow: 0 15px 35px rgba(0,0,0,0.5), 0 0 20px rgba(197, 168, 128, 0.1); border: 1px solid #c5a880; text-align: center; }
        h2, h3, .welcome-text { font-family: 'Playfair Display', serif; color: #e6c89c; letter-spacing: 1px; margin-top: 0; }
        .welcome-text { font-size: 24px; line-height: 1.2; margin-bottom: 5px; text-shadow: 0 2px 4px rgba(0,0,0,0.5); }
        .sub-welcome { color: #94a3b8; font-size: 11px; margin-bottom: 15px; letter-spacing: 2px; text-transform: uppercase; font-weight: 600; }
        
        /* Stats Bar */
        .user-stats { background: linear-gradient(90deg, #1e293b, #0f111a); padding: 10px; border-radius: 8px; border-left: 4px solid #e6c89c; display: flex; justify-content: space-around; margin-bottom: 20px; font-size: 14px; font-weight: bold; box-shadow: inset 0 2px 4px rgba(0,0,0,0.5); }
        .stat-val { color: #4ade80; }
        .xp-val { color: #facc15; }

        input, textarea { width: 88%; padding: 12px 15px; margin: 10px 0; border-radius: 6px; border: 1px solid #475569; background: #0f111a; color: #fff; font-family: 'Poppins', sans-serif; outline: none; }
        input:focus, textarea:focus { border-color: #e6c89c; box-shadow: 0 0 8px rgba(230, 200, 156, 0.3); }
        
        button { background: linear-gradient(45deg, #c5a880, #e6c89c); color: #0f111a; border: none; padding: 10px; width: 100%; border-radius: 6px; cursor: pointer; font-weight: 600; font-family: 'Poppins', sans-serif; text-transform: uppercase; transition: 0.3s; }
        button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(230, 200, 156, 0.4); }
        
        .section { display: none; animation: fadeIn 0.4s ease-in-out; }
        .active { display: block; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
        
        .nav-container { display: flex; justify-content: space-between; margin-bottom: 15px; }
        .nav-btn { background: transparent; color: #e6c89c; width: 23%; border: 1px solid #c5a880; font-size: 11px; padding: 8px 0; border-radius: 4px; }
        .nav-btn.active-btn { background: #c5a880; color: #0f111a; }
        
        .chat-box { height: 180px; overflow-y: auto; background: #0b0f19; padding: 10px; border-radius: 8px; text-align: left; font-size: 13px; margin-bottom: 15px; border: 1px solid #334155; }
        .msg { margin-bottom: 8px; border-bottom: 1px dashed #334155; padding-bottom: 5px; }
        .msg b { color: #e6c89c; }
        
        .notice-board { background: linear-gradient(135deg, #3d2a1d, #271c19); border-left: 3px solid #e6c89c; padding: 12px; border-radius: 4px; text-align: left; font-size: 13px; line-height: 1.5; }
        
        .status-box { margin-top: 15px; padding: 12px; background: #1e293b; border: 1px solid #475569; border-radius: 6px; font-size: 13px; text-align: left; }
        
        /* Leaderboard */
        .rank-item { display: flex; justify-content: space-between; background: #1e293b; padding: 10px; margin-bottom: 8px; border-radius: 6px; font-size: 13px; border: 1px solid #334155; }
        .rank-1 { border-color: #facc15; background: rgba(250, 204, 21, 0.1); }
        .rank-2 { border-color: #cbd5e1; background: rgba(203, 213, 225, 0.1); }
        .rank-3 { border-color: #b45309; background: rgba(180, 83, 9, 0.1); }
    </style>
</head>
<body>
    <div class="card">
        {% if status == 'approved' %}
            <div class="welcome-text">Qp 2.0 HUB</div>
            <div class="sub-welcome">Question Practices GC</div>
            
            <div class="user-stats">
                <div>Level: <span class="stat-val" id="my-level">--</span></div>
                <div>XP: <span class="xp-val" id="my-xp">--</span></div>
            </div>

            <div class="nav-container">
                <button class="nav-btn active-btn" onclick="showTab('home', this)">🏠 Home</button>
                <button class="nav-btn" onclick="showTab('chat', this)">💬 Chat</button>
                <button class="nav-btn" onclick="showTab('mock', this)">📝 Test</button>
                <button class="nav-btn" onclick="showTab('leader', this)">🏆 Rank</button>
            </div>

            <!-- Home Section -->
            <div id="home" class="section active">
                <h3 style="text-align: left;">📌 Notice Board</h3>
                <div class="notice-board" id="notice-list"></div>
                <a href="/logout"><button style="background: transparent; color: #ef4444; border: 1px solid #ef4444; margin-top: 25px;">Logout</button></a>
            </div>

            <!-- Chat Section -->
            <div id="chat" class="section">
                <h3 style="text-align: left;">💬 Group Chat</h3>
                <div class="chat-box" id="chat-box"></div>
                <input type="text" id="chat-input" placeholder="Message...">
                <button onclick="sendChat()">Send</button>
            </div>

            <!-- Mock Test Section -->
            <div id="mock" class="section">
                <h3 style="text-align: left;">📝 Submit Mock Test</h3>
                <textarea id="mock-ans" rows="4" placeholder="Your answer or Google Drive link..."></textarea>
                <button onclick="submitTest()">Submit</button>
                <div id="mock-status" class="status-box">Loading...</div>
            </div>

            <!-- Leaderboard Section -->
            <div id="leader" class="section">
                <h3 style="text-align: left; margin-bottom: 5px;">🏆 Global Leaderboard</h3>
                <p style="font-size: 11px; color: #94a3b8; text-align: left; margin-top: 0;">Complete tests & quizzes to rank up!</p>
                <div id="leaderboard-list" style="max-height: 250px; overflow-y: auto;">
                    Loading ranks...
                </div>
            </div>

            <script>
                function showTab(tab, btn) {
                    document.querySelectorAll('.section').forEach(el => el.classList.remove('active'));
                    document.getElementById(tab).classList.add('active');
                    document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active-btn'));
                    btn.classList.add('active-btn');
                }

                setInterval(() => {
                    fetch('/api/data').then(r => r.json()).then(data => {
                        // Update User Stats
                        document.getElementById('my-level').innerText = data.my_profile.level;
                        document.getElementById('my-xp').innerText = data.my_profile.points;

                        // Notice & Chats
                        document.getElementById('notice-list').innerHTML = data.notices.map(n => `<p>✨ ${n}</p>`).join('');
                        document.getElementById('chat-box').innerHTML = data.chats.map(c => `<div class="msg"><b>${c.uid}:</b> ${c.text}</div>`).join('');
                        
                        // Mock Status
                        const mStatus = data.mock;
                        let mHtml = "<b style='color:#94a3b8;'>Status:</b> No submission.";
                        if(mStatus.status === 'submitted') mHtml = "<b style='color:#facc15;'>Status:</b> ⏳ Pending review.";
                        if(mStatus.status === 'checked') mHtml = `<b style='color:#e6c89c;'>Status:</b> ✅ Checked!<br><br><span style="color:#fff;"><b>Result:</b> ${mStatus.result}</span>`;
                        document.getElementById('mock-status').innerHTML = mHtml;

                        // Leaderboard
                        let lbHtml = "";
                        data.leaderboard.forEach((u, i) => {
                            let rClass = i === 0 ? 'rank-1' : (i === 1 ? 'rank-2' : (i === 2 ? 'rank-3' : ''));
                            lbHtml += `<div class="rank-item ${rClass}">
                                <span><b>#${i+1}</b> ${u.uid} (Lv. ${u.level})</span>
                                <span style="color:#facc15; font-weight:bold;">${u.points} XP</span>
                            </div>`;
                        });
                        document.getElementById('leaderboard-list').innerHTML = lbHtml || "No ranked users yet.";
                    });
                }, 3000);

                function sendChat() {
                    const text = document.getElementById('chat-input').value;
                    if(!text) return;
                    fetch('/api/send_chat', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({text}) });
                    document.getElementById('chat-input').value = '';
                }

                function submitTest() {
                    const ans = document.getElementById('mock-ans').value;
                    if(!ans) return alert("Please enter your answer!");
                    fetch('/api/submit_test', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ans}) })
                    .then(() => { alert("Submitted!"); document.getElementById('mock-ans').value = ''; });
                }
            </script>

        {% elif status == 'pending' %}
            <h3 style="color: #e6c89c;">⏳ Pending</h3>
            <p style="color: #94a3b8; font-size: 14px;">Waiting for admin approval...</p>
            <script>setInterval(() => { fetch('/status').then(r => r.json()).then(d => { if(d.status !== 'pending') location.reload(); }); }, 3000);</script>
        {% elif status == 'rejected' %}
            <h3 style="color: #ef4444;">❌ Access Denied</h3>
            <a href="/logout"><button>Try Again</button></a>
        {% else %}
            <h2 style="font-size: 28px; margin-bottom: 5px;">Qp 2.0 HUB</h2>
            <p style="font-size: 11px; color: #94a3b8; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 30px;">Members Secure Login</p>
            <p style="font-size: 13px; color: #cbd5e1; text-align: left;">Enter Username / ID:</p>
            <form method="POST" action="/login">
                <input type="text" name="user_id" placeholder="e.g. @username or 123456" required>
                <button type="submit" style="margin-top: 10px;">Login</button>
            </form>
        {% endif %}
    </div>
</body>
</html>
"""

def req_tg(method, data):
    try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/{method}", json=data)
    except: pass

def update_points(uid, pts):
    if uid not in user_profiles:
        user_profiles[uid] = {"points": 0, "level": 1}
    user_profiles[uid]["points"] += pts
    # প্রতি ১০০ পয়েন্টে ১ লেভেল আপ হবে (১০০ XP = Level 2, ২০০ XP = Level 3)
    user_profiles[uid]["level"] = (user_profiles[uid]["points"] // 100) + 1

def bot_listener():
    offset = 0
    while True:
        try:
            res = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}&timeout=10").json()
            for update in res.get("result", []):
                offset = update["update_id"] + 1
                
                # লগইন অ্যাপ্রুভাল
                if "callback_query" in update:
                    call = update["callback_query"]
                    if str(call["from"]["id"]) == str(ADMIN_CHAT_ID):
                        act, uid = call["data"].split("_", 1)
                        users_status[uid] = "approved" if act == "ok" else "rejected"
                        if act == "ok" and uid not in user_profiles:
                            user_profiles[uid] = {"points": 0, "level": 1} # নতুন ইউজার প্রোফাইল তৈরি
                        msg = f"✅ User {uid} Approved!" if act == "ok" else f"❌ User {uid} Rejected!"
                        req_tg("editMessageText", {"chat_id": ADMIN_CHAT_ID, "message_id": call["message"]["message_id"], "text": msg})
                
                # অ্যাডমিন মেসেজ হ্যান্ডেলিং
                if "message" in update and str(update["message"]["from"]["id"]) == str(ADMIN_CHAT_ID):
                    msg_text = update["message"].get("text", "")
                    
                    # নোটিশ যোগ করা
                    if msg_text.startswith("/notice "):
                        notices.insert(0, msg_text.replace("/notice ", ""))
                        req_tg("sendMessage", {"chat_id": ADMIN_CHAT_ID, "text": "✅ Notice Added!"})
                    
                    # ম্যানুয়ালি কুইজ পয়েন্ট যোগ করা (e.g., /addpoint @username 20)
                    elif msg_text.startswith("/addpoint "):
                        parts = msg_text.split()
                        if len(parts) >= 3:
                            t_uid = parts[1]
                            pts = int(parts[2])
                            update_points(t_uid, pts)
                            req_tg("sendMessage", {"chat_id": ADMIN_CHAT_ID, "text": f"✅ Added {pts} XP to {t_uid}! They are now Level {user_profiles[t_uid]['level']}."})

                    # মক টেস্ট খাতা দেখা ও পয়েন্ট দেওয়া
                    elif "reply_to_message" in update["message"]:
                        orig_text = update["message"]["reply_to_message"].get("text", "")
                        if "Mock Test from User:" in orig_text:
                            uid = orig_text.split("User:")[1].strip().split()[0]
                            if uid in mock_results:
                                # মেসেজ থেকে নম্বর (সংখ্যা) খুঁজে বের করে পয়েন্ট হিসেবে যোগ করা
                                match = re.search(r'\b\d+\b', msg_text)
                                marks = int(match.group()) if match else 0
                                
                                if marks > 0: update_points(uid, marks)
                                
                                mock_results[uid]["status"] = "checked"
                                mock_results[uid]["result"] = msg_text
                                req_tg("sendMessage", {"chat_id": ADMIN_CHAT_ID, "text": f"✅ Result sent to {uid}! Awarded {marks} XP."})
        except: pass
        time.sleep(1)

@app.route("/")
def home():
    uid = session.get("uid")
    return render_template_string(HTML_PAGE, status=users_status.get(uid))

@app.route("/login", methods=["POST"])
def login():
    uid = request.form.get("user_id").strip()
    session["uid"] = uid
    users_status[uid] = "pending"
    
    kb = {"inline_keyboard": [[{"text": "✅ Approve", "callback_data": f"ok_{uid}"}, {"text": "❌ Reject", "callback_data": f"no_{uid}"}]]}
    req_tg("sendMessage", {"chat_id": ADMIN_CHAT_ID, "text": f"🔔 Login Request!\nUser: `{uid}`", "parse_mode": "Markdown", "reply_markup": kb})
    return redirect(url_for("home"))

@app.route("/status")
def status(): return jsonify({"status": users_status.get(session.get("uid"), "none")})

@app.route("/logout")
def logout():
    session.pop("uid", None)
    return redirect(url_for("home"))

@app.route("/api/data")
def api_data():
    uid = session.get("uid")
    if not uid or users_status.get(uid) != "approved": return jsonify({})
    
    # Leaderboard Sorting (Highest points first)
    sorted_users = sorted([{"uid": k, **v} for k, v in user_profiles.items()], key=lambda x: x["points"], reverse=True)
    
    my_prof = user_profiles.get(uid, {"points": 0, "level": 1})
    m_stat = mock_results.get(uid, {"status": "none"})
    
    return jsonify({
        "notices": notices, 
        "chats": chat_messages[-25:], 
        "mock": m_stat,
        "my_profile": my_prof,
        "leaderboard": sorted_users
    })

@app.route("/api/send_chat", methods=["POST"])
def api_send_chat():
    uid = session.get("uid")
    if uid and users_status.get(uid) == "approved":
        chat_messages.append({"uid": uid, "text": request.json.get("text")})
    return "OK"

@app.route("/api/submit_test", methods=["POST"])
def api_submit_test():
    uid = session.get("uid")
    if uid and users_status.get(uid) == "approved":
        ans = request.json.get("ans")
        mock_results[uid] = {"status": "submitted", "ans": ans, "result": ""}
        text = f"📝 *Mock Test from User:* `{uid}`\n\n*Answer:*\n{ans}\n\n👉 _Reply with marks (e.g. '85 Good job') to assign XP._"
        req_tg("sendMessage", {"chat_id": ADMIN_CHAT_ID, "text": text, "parse_mode": "Markdown"})
    return "OK"

if __name__ == "__main__":
    threading.Thread(target=bot_listener, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
    
