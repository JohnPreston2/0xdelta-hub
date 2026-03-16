#!/usr/bin/env python3
import requests
import json
import hashlib
import subprocess
import re
import os
import time
from datetime import datetime, timezone

VENICE_API_KEY = "VENICE-ADMIN-KEY-ZyuRVusgiVIaSm6FoudtSNH2wj4ktVj4vaqO1sAkyH"
VENICE_URL = "https://api.venice.ai/api/v1/chat/completions"
TELEGRAM_BOT_TOKEN = "8354716169:AAGB54HoOQeP1y3EkX7lwJoT4dPlB89Na38"
TELEGRAM_CHAT_ID = "1321582287"
MOLTBOOK_API_KEY = "moltbook_sk__ZR7uTCWam1OVSVKyEQEBNgSX0jv6ycG"
MOLTBOOK_URL = "https://www.moltbook.com/api/v1/posts"

SYNTHESIS_OUTPUT = "/tmp/0xdelta-hub/synthesis.json"
BANKR_PATH = "/home/classics2323/.openclaw/workspace/skills/bankr/scripts/bankr.sh"
FORENSIC_WALLET = "0xEb18a33e8F9517EC1D2888267540029e126a3054"
POSITION_FILE = "/home/classics2323/.openclaw/workspace/mind/position.json"

def load_prompt():
    with open("/home/classics2323/crypto-monitor/PROMPT_ANALYSIS.md") as f:
        return f.read()

def load_forensic_reports():
    processed_dir = "/home/classics2323/crypto-monitor/data/processed"
    files = sorted([f for f in os.listdir(processed_dir) if f.startswith("forensic_")])
    if not files: return None, None
    with open(os.path.join(processed_dir, files[-1])) as f: current = json.load(f)
    previous = None
    if len(files) > 1:
        with open(os.path.join(processed_dir, files[-2])) as f: previous = json.load(f)
    return current, previous

def build_synthesis_json(current, analysis, seal_hash=None, tx_hash=None):
    tokens = current.get("tokens", {})
    token_list = []
    for addr, t in tokens.items():
        conv = t.get("convergence", {})
        token_list.append({
            "symbol": t.get("symbol", addr[:8]),
            "address": addr,
            "fhs": conv.get("fhs", 0),
            "ces": conv.get("ces", 0),
            "phase": conv.get("phase", ""),
            "nbp": t.get("flows", {}).get("nbp", 0),
            "bpi": t.get("bull_flag", {}).get("bpi", 0)
        })
    synthesis = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "synthesis_table": token_list,
        "raw_report": analysis,
        "seal": {"report_hash": seal_hash, "tx_hash": tx_hash} if seal_hash else None
    }
    return synthesis

def check_and_exit_position():
    if not os.path.exists(POSITION_FILE): return
    try:
        with open(POSITION_FILE, 'r') as f: pos = json.load(f)
        if pos.get("status") == "OPEN" and (time.time() - pos.get("entry_time", 0)) >= 5400:
            print(f"⏳ TIMEOUT (90min) pour {pos['symbol']}. Exit...")
            subprocess.run([BANKR_PATH, f"Sell 100% of my {pos['symbol']} ({pos['address']}) for ETH on Base"], capture_output=True)
            with open(POSITION_FILE, 'w') as f: json.dump({"status": "CLOSED", "last_symbol": pos['symbol']}, f)
    except: pass

def seal_report_onchain(text):
    report_hash = hashlib.sha256(text.encode()).hexdigest()
    cmd = f"bash {BANKR_PATH} \"Send 0 ETH to 0x8004A169FB4a3325136EB29fA0ceB6D2e539a432 on Base with data 0x{report_hash}\""
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    tx_hash = re.search(r'basescan\.org/tx/(0x[a-fA-F0-9]+)', res.stdout)
    return report_hash, tx_hash.group(1) if tx_hash else None

def enter_new_position(text, current_data):
    if os.path.exists(POSITION_FILE):
        with open(POSITION_FILE, 'r') as f:
            if json.load(f).get("status") == "OPEN": return
    match = re.search(r'\$([a-zA-Z0-9]{2,10})', text)
    if match:
        symbol = match.group(1).upper()
        addr = next((a for a, i in current_data.get("tokens", {}).items() if i.get("symbol") == symbol), None)
        if addr:
            subprocess.run([BANKR_PATH, f"Swap 75% of my ETH balance for {symbol} ({addr}) on Base"], capture_output=True)
            with open(POSITION_FILE, 'w') as f: json.dump({"symbol": symbol, "address": addr, "entry_time": time.time(), "status": "OPEN"}, f)

def main():
    check_and_exit_position()
    current, _ = load_forensic_reports()
    if not current: return
    prompt = load_prompt()
    payload = {"model": "gemini-3-flash-preview", "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": f"Analyze: {json.dumps(current, indent=None)}"}], "max_tokens": 4000}
    r = requests.post(VENICE_URL, headers={"Authorization": f"Bearer {VENICE_API_KEY}", "Content-Type": "application/json"}, json=payload, timeout=300)
    analysis = r.json()["choices"][0]["message"]["content"] if r.status_code == 200 else None
    if analysis:
        h, tx = seal_report_onchain(analysis)
        analysis += f"\n\n🔐 **SEALED ONBASE**: 0x{h[:16]}... (TX: {tx if tx else 'Pending'})"
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={"chat_id": TELEGRAM_CHAT_ID, "text": analysis})
        synthesis = build_synthesis_json(current, analysis, h, tx)
        os.makedirs(os.path.dirname(SYNTHESIS_OUTPUT), exist_ok=True)
        with open(SYNTHESIS_OUTPUT, "w") as f: json.dump(synthesis, f, indent=2)
        subprocess.run(["curl", "-s", "-X", "POST", MOLTBOOK_URL, "-H", f"Authorization: Bearer {MOLTBOOK_API_KEY}", "-H", "Content-Type: application/json", "-d", json.dumps({"submolt_name":"trading", "title":"Pulse Report", "content": analysis[:400]})])
        enter_new_position(analysis, current)

if __name__ == "__main__": main()
