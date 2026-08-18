import litellm
import json
import re
import sys

SYSTEM_PROMPT = """You are a code security reviewer. Respond ONLY with valid JSON in this exact format:
{"verdict": "pass" or "fail", "issues": ["list of issues found"]}
No explanation, no markdown, just the JSON object."""


def _extract_json(raw_text: str) -> dict:
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not match:
        raise json.JSONDecodeError("No JSON object found", raw_text, 0)
    return json.loads(match.group(0))


def review_security(diff_text: str) -> dict:
    try:
        response = litellm.completion(
            model="ollama/qwen2.5-coder:7b",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Review this code diff:\n{diff_text}"}
            ],
            temperature=0,
            timeout=180,
        )
    except Exception as e:
        return {"verdict": "error", "issues": [f"Agent call failed: {str(e)}"]}

    try:
        return _extract_json(response.choices[0].message.content)
    except json.JSONDecodeError:
        return {"verdict": "error", "issues": ["Model returned invalid JSON"]}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agents/security_agent.py <path_to_diff.txt>")
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        diff = f.read()
    print(review_security(diff))