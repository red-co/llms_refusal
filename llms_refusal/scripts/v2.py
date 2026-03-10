import requests
import json
from pathlib import Path
from datetime import datetime
import logging

# Assuming these global variables are already defined (inherited from previous code)
LOG_DIR       = Path("./logs")
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
LLM_SERVER_URL = "http://127.0.0.1:8080/v1/chat/completions"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer no-key-needed"
}
MODEL_NAME = "your-model.gguf"  # Please replace with the actual model name

CHECK_PROMPT_DIR = Path("./check_prompt")
V2_RESULT_MD = CHECK_PROMPT_DIR / "v2.md"


def revalidate_all_check_prompts() -> None:
    """
    Reads all check_prompt_*.txt files in the ./check_prompt/ directory,
    re-requests the model to validate the content of each file,
    and aggregates the results into ./check_prompt/v2.md
    """
    logger.info("Starting secondary validation of all saved check_prompts")

    # Collect all check_prompt files
    prompt_files = sorted(
        CHECK_PROMPT_DIR.glob("check_prompt_*.txt"),
        key=lambda p: p.name
    )

    if not prompt_files:
        logger.warning("No check_prompt_*.txt files found in the check_prompt directory")
        return

    results = []
    total = len(prompt_files)

    # If v2.md already exists, backup or clear it first (here we choose to append with a separator)
    if V2_RESULT_MD.exists():
        with V2_RESULT_MD.open("a", encoding="utf-8") as f:
            f.write("\n\n---\n\nSecondary validation started at " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n")

    else:
        header = (
            "# Secondary Validation Results Summary (v2)\n\n"
            "Time of this secondary validation: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n"
            "| Index | Filename | Brief Original Requirement | Secondary Validation Answer | Passed (y/n) |\n"
            "|------|----------|----------------------------|-----------------------------|---------------|\n"
        )
        V2_RESULT_MD.write_text(header, encoding="utf-8")

    for idx, file_path in enumerate(prompt_files, 1):
        try:
            check_prompt = file_path.read_text(encoding="utf-8").strip()
            if not check_prompt:
                print("not check prompt")
                continue

            # Extract brief description (first line is usually "Executed requirement: xxx")
            first_line = check_prompt.splitlines()[0][:80] + "..." if len(check_prompt.splitlines()) > 0 else ""

            logger.info(f"[{idx}/{total}] Secondary validating: {file_path.name}")

            # Construct validation payload (same as the previous second request)
            payload = {
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": check_prompt}],
                "temperature": 0.1,
                "max_tokens": 30,
                "stream": False
            }

            response = requests.post(
                LLM_SERVER_URL,
                json=payload,
                headers=HEADERS,
                timeout=45
            )
            response.raise_for_status()
            print(response.status_code)
            print(response.text)

            # ... Previous code remains unchanged ...

            answer = response.json()["choices"][0]["message"]["content"].strip()
            answer_lower = answer.lower()

            passed = 'y' if 'yes' in answer_lower else 'n'

            # First handle escaping
            safe_answer = answer.replace('|', r'\|')[:120]

            # Then construct the row
            row = (
                f"| {idx} | {file_path.name} | "
                f"{first_line} | "
                f"`{safe_answer}` | **{passed}** |\n"
            )

            with V2_RESULT_MD.open("a", encoding="utf-8") as f:
                f.write(row)
            results.append(passed)
            logger.info(f"  → Answer: {answer}")

        except Exception as e:
            error_msg = f"Secondary validation failed for {file_path.name}: {str(e)}"
            logger.error(error_msg)

            row = f"| {idx} | {file_path.name} | - | **Error** | n |\n"
            with V2_RESULT_MD.open("a", encoding="utf-8") as f:
                f.write(row)

            results.append('n')

    # Summary statistics
    success_count = results.count('y')
    summary = (
        f"\nSecondary validation completed (Total: {total} items)\n"
        f"Passed count: {success_count} / {total} ({success_count/total*100:.1f}%)\n"
        f"Ratio of 'y': {success_count/total*100:.1f}%\n"
    )

    with V2_RESULT_MD.open("a", encoding="utf-8") as f:
        f.write("\n" + summary)

    logger.info(summary)
    logger.info(f"Secondary validation results written to: {V2_RESULT_MD}")


# If you want to run this function directly, call it like this:
if __name__ == "__main__":
    revalidate_all_check_prompts()
