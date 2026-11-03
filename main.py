import os
import time
import threading
import subprocess
from flask import Flask, send_from_directory, request, jsonify

app = Flask(__name__)

bot_process = None
is_monitoring = False

def auto_restart_monitor():
    global bot_process, is_monitoring
    print("[MONITOR] Auto Re-trigger Background Thread Start Ho Gaya Hai.")
    while is_monitoring:
        if bot_process is None or bot_process.poll() is not None:
            print("[MONITOR] Match offline ho gaya hai. Wapas same region se restart kiya ja raha hai...")
            time.sleep(5)
            # Original start.py ko dubara trigger karna
            bot_process = subprocess.Popen(["python3", "start.py"])
            print("[MONITOR] Tool safaltapoorvak dubara on ho gaya.")
        time.sleep(10)

@app.route('/')
def serve_hammad():
    return send_from_directory('HAMMAD', 'index.html')

# Step 1: Account Creation (Saves to accs.txt)
@app.route('/step1-create', methods=['POST'])
def step1_create():
    base_username = request.form.get('base_username')
    password = request.form.get('password')
    count = int(request.form.get('count', 1))
    
    created_accounts = []
    with open("accs.txt", "a") as f:
        for i in range(1, count + 1):
            username = f"{base_username}_{i}" if count > 1 else base_username
            f.write(f"{username}:{password}\n")
            created_accounts.append(username)
            
    print(f"[STEP 1] Successfully generated {count} accounts in accs.txt")
    return jsonify({
        "status": "success", 
        "message": f"Total {count} accounts successfully create ho gaye hain!",
        "accounts": created_accounts
    })

# Step 2: Guild Join (Connected with tool config/arguments)
@app.route('/step2-guild', methods=['POST'])
def step2_guild():
    guild_id = request.form.get('guild_id')
    print(f"[STEP 2] Guild join request received for ID: {guild_id}")
    
    try:
        # Agar aapka tool koi command-line argument ya config file accept karta hai guild ke liye,
        # toh use yahan pass kar sakte hain. Filhal ye match.py / tool ko guild ID ke sath call karega.
        if os.path.exists("match.py"):
            subprocess.run(["python3", "match.py", "--guild", guild_id], check=True)
            return jsonify({"status": "success", "message": f"Guild ID {guild_id} par accounts successfully join ho gaye hain!"})
        else:
            return jsonify({"status": "success", "message": f"Guild ID {guild_id} queued for accounts in accs.txt!"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Guild join error: {str(e)}"})

# Step 3: Match Start & Auto-Re-trigger Loop
@app.route('/step3-match', methods=['POST'])
def step3_match():
    global bot_process, is_monitoring
    if not is_monitoring:
        is_monitoring = True
        print("[STEP 3] Match tool pehle baar launch kiya ja raha hai...")
        bot_process = subprocess.Popen(["python3", "start.py"])
        
        # Background thread jo 10 min baad offline hone par khud on kar dega
        monitor_thread = threading.Thread(target=auto_restart_monitor, daemon=True)
        monitor_thread.start()
        
        return jsonify({"status": "success", "message": "Match start ho gaya hai aur Auto-Re-trigger monitor active hai!"})
    
    return jsonify({"status": "info", "message": "Match tool pehle se hi running state me hai!"})

# Step 4: Delete Accounts (rm -rf accs.txt)
@app.route('/delete-accounts', methods=['POST'])
def delete_accounts():
    print("[DELETE] Saare accounts delete kiye ja rahe hain via rm -rf...")
    os.system("rm -rf accs.txt")
    return jsonify({"status": "success", "message": "accs.txt file aur saare accounts successfully delete ho gaye hain!"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
