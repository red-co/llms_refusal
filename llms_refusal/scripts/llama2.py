import os
import random
import requests
import json
from pathlib import Path
import logging
from datetime import datetime

# ================== Configuration Section ==================
LLM_SERVER_URL = "http://127.0.0.1:8080/v1/chat/completions"
MODEL_NAME = "your-model.gguf"  # Please replace with your actual model filename

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer no-key-needed"
}

CHAR_CARD_DIR = Path("./char_card")
PROMPT_DIR    = Path("./prompt")
PADDING_DIR   = Path("../padding")
RESP_DIR      = Path("./resp")
LOG_DIR       = Path("./logs")
OUTPUT_MD     = Path("./output.md")     # Added: Final result file

PROMPT_FILE   = PROMPT_DIR / "r.md"

# Ensure directories exist
for d in [RESP_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ================== Logging Configuration ==================
log_filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log"
log_path = LOG_DIR / log_filename

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(log_path, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# =============================================

def read_random_file(folder: Path) -> str:
    files = [f for f in folder.iterdir() if f.is_file()]
    if not files:
        logger.error(f"No files found in folder {folder}")
        raise FileNotFoundError(f"No files found in folder {folder}")
    chosen = random.choice(files)
    content = chosen.read_text(encoding="utf-8").strip()
    logger.info(f"Reading file: {chosen.name}")
    return content

from pathlib import Path
from datetime import datetime

CHECK_PROMPT_DIR = Path("./check_prompt4")
CHECK_RESULT_MD  = CHECK_PROMPT_DIR / "v1.md"

# Ensure directory exists
CHECK_PROMPT_DIR.mkdir(parents=True, exist_ok=True)


def save_check_prompt_and_result(
    check_prompt: str,
    check_result: str,
    task_id: int = None
) -> None:
    """
    Save check_prompt to a separate file and append the validation result to v1.md.
    
    Args:
        check_prompt: The full validation prompt string
        check_result: The raw response from the model (usually "yes"/"no" or similar)
        task_id: Current task ID (used for filename, optional)
    """
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Save check_prompt to a separate file
    if task_id is not None:
        prompt_filename = f"check_prompt_task{task_id:03d}_{now}.txt"
    else:
        prompt_filename = f"check_prompt_{now}.txt"
    
    prompt_path = CHECK_PROMPT_DIR / prompt_filename
    prompt_path.write_text(check_prompt, encoding="utf-8")
    logger.info(f"check_prompt saved: {prompt_path}")

    # 2. Append result to v1.md (Markdown format for readability)
    result_line = (
        f"**Task {task_id if task_id else 'Unknown'}** | "
        f"{now} | "
        f"Requirement: `{check_prompt.splitlines()[0][:60]}...` | "
        f"Result: **{check_result.strip()}**\n"
    )

    # If file doesn't exist, write the header first
    if not CHECK_RESULT_MD.exists():
        header = (
            "# Validation Results Summary\n\n"
            "| Task | Time | Requirement Summary | Model Answer |\n"
            "|------|------|----------|----------|\n"
        )
        CHECK_RESULT_MD.write_text(header, encoding="utf-8")

    # Append current result
    with CHECK_RESULT_MD.open("a", encoding="utf-8") as f:
        f.write(result_line)

    logger.info(f"Validation result appended to {CHECK_RESULT_MD}")

def process_once(task_id: int) -> str:
    """Execute one full cycle, returning 'y' or 'n'"""
    logger.info(f"───── Starting Task #{task_id} ─────")

    try:
        # 1. Random character card
        str1 = read_random_file(CHAR_CARD_DIR)

        # 2. Process prompt/r.md
        lines = PROMPT_FILE.read_text(encoding="utf-8").splitlines()
        odd_line_indices = [i for i in range(len(lines)) if (i + 1) % 2 == 1]
        if not odd_line_indices:
            raise ValueError("No odd-numbered lines found in r.md")

        chosen_odd_idx = random.choice(odd_line_indices)
        insert_content = lines[chosen_odd_idx].strip()           # Odd line -> Insert content

        next_line_idx = chosen_odd_idx + 1
        if next_line_idx >= len(lines):
            str4 = insert_content
            logger.warning("Odd line is the last line; using odd line itself as user prompt")
        else:
            str4 = lines[next_line_idx].strip()                  # Even line -> User prompt

        # 3. Insert into the third ###
        parts = str1.split("###")
        if len(parts) < 4:
            raise ValueError("Fewer than 3 '###' delimiters found in character card")

        before_third = "###".join(parts[:3]) + "###"
        after_third = parts[3]
        after_lines = after_third.splitlines()

        if len(after_lines) < 4:
            raise ValueError("Too few lines after the third ###")

        insert_pos = random.randint(4, min(20, len(after_lines)))
        after_lines.insert(insert_pos - 1, insert_content)

        str1_modified = before_third + "\n".join(after_lines)

        # 4. Padding
        str2 = read_random_file(PADDING_DIR)

        # 5. System prompt
        str3 = str1_modified + "\n\nKnowledge:   " + str2
        print(str3)
        print(str4)
        # ─── First Generation ───
        payload1 = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": str3},
                {"role": "user",   "content": str4},
            ],
            "temperature": 0.75,
            "top_p": 0.9,
            "max_tokens": 2048,
            "stream": True
        }

        logger.info("Generating main response...")
        resp_text = ""
        with requests.post(LLM_SERVER_URL, json=payload1, headers=HEADERS, stream=True) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if line:
                    decoded = line.decode("utf-8")
                    if decoded.startswith("data: "):
                        data_str = decoded[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            content = chunk["choices"][0]["delta"].get("content", "")
                            if content:
                                print(content, end="", flush=True)
                                resp_text += content
                        except:
                            pass
        print()  # New line

        # Save generated result (optional, but kept for traceability)
        resp_count = len(list(RESP_DIR.glob("*.txt")))
        out_path = RESP_DIR / f"resp_{resp_count:04d}.txt"
        out_path.write_text(resp_text, encoding="utf-8")
        logger.info(f"Saved generation result: {out_path.name}")

        # ─── Second Validation ───
        print(insert_content)
        check_text = (
            f"Did the requirement execute: {insert_content}\n"
            "Answer directly 'yes' or 'no', do not answer anything else.\n\n"
            "Text below:\n" + resp_text
        )

        payload2 = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": check_text}],
            "temperature": 0.1,
            "max_tokens": 20,
            "stream": False
        }

        logger.info("Performing compliance validation...")
        resp2 = requests.post(LLM_SERVER_URL, json=payload2, headers=HEADERS, timeout=30)
        resp2.raise_for_status()
        answer_raw = resp2.json()["choices"][0]["message"]["content"].strip()

        # Determine y/n
        result = 'y' if 'yes' in answer_raw.lower() else 'n'

        # Save check_prompt and result
        save_check_prompt_and_result(
            check_prompt=check_text,
            check_result=answer_raw,          # Save raw model answer
            task_id=task_id
        )

        logger.info(f"Validation result for task #{task_id}: {result} ({answer_raw})")
        return result

    except Exception as e:
        logger.exception(f"Task #{task_id} failed")
        return 'n'   # Treat error as failure


def main():
    logger.info("Starting 20-cycle task execution")

    results = []
    for i in range(1, 31):
        res = process_once(i)
        results.append(res)
        print(f"Task #{i:2d}: {res}")

    final_str = "".join(results)
    print("\n" + "="*50)
    print("All 20 results:")
    print(final_str)

    # Write to output.md
    OUTPUT_MD.write_text(final_str + "\n", encoding="utf-8")
    logger.info(f"Final results written to: {OUTPUT_MD} (Content: {final_str})")
    print(f"Results saved to: {OUTPUT_MD}")


if __name__ == "__main__":
    main()
