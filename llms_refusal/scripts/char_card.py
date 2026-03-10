import os
import json
import requests
import time
from pathlib import Path

# -----------------------------
# comfig
# -----------------------------
LLAMA_URL = "http://127.0.0.1:8080/v1/chat/completions"
SAVE_DIR = Path("./char_card")
TARGET_COUNT = 20
MODEL_NAME = "local-model"

PROMPT = """
Randomly generate 1 character card.
No dialogue settings required.

Character
- Name
- Occupation
- Age
- Appearance
- Personality

- 32 tasks
- 32 things to avoid doing
- 16 dislikes
"""

# -----------------------------
# server handshake
# -----------------------------
def check_server():
    try:
        r = requests.get("http://127.0.0.1:8080/health", timeout=5)
        if r.status_code == 200:
            print("llama.cpp server health")
            return True
    except Exception:
        pass
    print("error to connect llama.cpp server")
    return False

# -----------------------------
# check cards
# -----------------------------
def count_cards():
    SAVE_DIR.mkdir(exist_ok=True)
    return len(list(SAVE_DIR.glob("*.txt")))

# -----------------------------
# streaming 
# -----------------------------
def generate_stream(file_path):
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": PROMPT}],
        "temperature": 0.9,
        "stream": True
    }

    with requests.post(LLAMA_URL, json=payload, stream=True, timeout=600) as r, open(file_path, "w", encoding="utf-8") as f:
        r.raise_for_status()
        token_count = 0
        start = time.time()

        for line in r.iter_lines():
            if not line:
                continue
            if not line.startswith(b"data: "):
                continue

            data = line[6:].strip()
            if data == b"[DONE]":
                break

            try:
                j = json.loads(data)
            except Exception:
                continue

            delta = j.get("choices", [{}])[0].get("delta", {})
            token = delta.get("content")
            if isinstance(token, str):
                f.write(token)
                f.flush()  
                token_count += 1

                elapsed = time.time() - start
                tps = token_count / elapsed if elapsed > 0 else 0
                ctx = j.get("usage", {}).get("total_tokens", 0)  
                print(f"\rtokens:{token_count} speed:{tps:.2f} t/s ctx:{ctx}", end="", flush=True)

        print()  
    return token_count

# -----------------------------
# 
# -----------------------------
def main():
    if not check_server():
        return

    existing = count_cards()
    if existing >= TARGET_COUNT:
        print(f"{existing} character cards already exist, skipping generation")
        return

    need = TARGET_COUNT - existing
    print(f"There are already {existing} character cards, need to generate {need} more")

    for i in range(existing, TARGET_COUNT):
        print(f"\nGenerating {i+1}/{TARGET_COUNT}")
        file_path = SAVE_DIR / f"char_{i:03d}.txt"
        try:
            tokens = generate_stream(file_path)
            print(f" tokens:{tokens}")
        except Exception as e:
            print("error:", e)
            time.sleep(3)
            continue

    print("\nCompleted")

if __name__ == "__main__":
    main()