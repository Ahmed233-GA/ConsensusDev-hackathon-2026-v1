import litellm
import json
import re
import sys

SYSTEM_PROMPT = """You are a reviewer checking if code changes match their assigned task. Compare the code diff against the ticket description and judge whether the implementation actually fulfills what was asked. Respond ONLY with valid JSON in this exact format:
{"verdict": "pass" or "fail", "issues": ["list of mismatches found"]}
No explanation, no markdown, just the JSON object."""


def _extract_json(raw_text: str) -> dict:
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not match:
        raise json.JSONDecodeError("No JSON object found", raw_text, 0)
    return json.loads(match.group(0))


def review_story_match(diff_text: str, ticket_description: str) -> dict:
    try:
        response = litellm.completion(
            model="ollama/qwen2.5-coder:7b",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Ticket description:\n{ticket_description}\n\nCode diff:\n{diff_text}"}
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
    if len(sys.argv) < 3:
        print("Usage: python agents/story_match_agent.py <path_to_diff.txt> <path_to_ticket.txt>")
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        diff = f.read()
    with open(sys.argv[2], "r", encoding="utf-8") as f:
        ticket = f.read()
    print(review_story_match(diff, ticket)) #Needs the diff and the ticket files to work properly