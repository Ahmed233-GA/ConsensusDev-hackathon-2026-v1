# ============================================================
# AGENT TEMPLATE — copy this file, rename it, and change only
# the two marked sections (SYSTEM_PROMPT and the function name)
# to create a new agent.
# ============================================================

import litellm      # The library that lets us call any LLM (Ollama, OpenAI, etc.) with one consistent interface
import json          # Used to parse the model's text response into a real Python dictionary
import re             # Used to find/extract the JSON object even if the model adds extra text around it
import sys           # Lets this script read arguments from the command line (e.g. a file path)


# ------------------------------------------------------------
# 1) SYSTEM PROMPT — this is the agent's "job description."
#    Change this text for each different agent (Security,
#    Performance, etc). Keep the JSON format instruction
#    identical across all agents so they're easy to merge later.
# ------------------------------------------------------------
SYSTEM_PROMPT = """You are a [ROLE — e.g. code security reviewer]. 
Check for: [list the specific things this agent should look for].
Respond ONLY with valid JSON in this exact format:
{"verdict": "pass" or "fail", "issues": ["list of issues found"]}
No explanation, no markdown, just the JSON object."""


# ------------------------------------------------------------
# 2) JSON EXTRACTOR — a helper function, reused by every agent.
#    Models sometimes wrap their JSON in extra text like
#    "Here is the review: {...}" — this pulls just the {...}
#    part out with a regex, so json.loads() doesn't crash.
# ------------------------------------------------------------
def _extract_json(raw_text: str) -> dict:
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)   # re.DOTALL lets the match span multiple lines
    if not match:
        # If no {...} was found at all, raise a clear error instead of crashing mysteriously later
        raise json.JSONDecodeError("No JSON object found", raw_text, 0)
    return json.loads(match.group(0))   # Convert the matched text into a real Python dict


# ------------------------------------------------------------
# 3) THE AGENT FUNCTION — this is what other files (run_all.py,
#    main.py) will import and call. Rename this function for
#    each agent, e.g. review_security, review_performance, etc.
#    diff_text: the raw code diff to review (a plain string)
# ------------------------------------------------------------
def review_TEMPLATE(diff_text: str) -> dict:

    # --- Step A: try to call the model ---
    try:
        response = litellm.completion(
            model="ollama/qwen2.5-coder:7b",   # Which local model to use — swap this to tune speed vs accuracy
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},                      # The agent's instructions
                {"role": "user", "content": f"Review this code diff:\n{diff_text}"} # The actual code to check
            ],
            temperature=0,     # 0 = as deterministic/consistent as possible (less random guessing)
            timeout=180,       # Give up after 180 seconds if the model never responds (prevents hanging forever)
        )
    except Exception as e:
        # If Ollama isn't running, the model isn't pulled, or the call times out —
        # return a safe "error" result instead of crashing the whole pipeline.
        return {"verdict": "error", "issues": [f"Agent call failed: {str(e)}"]}

    # --- Step B: try to parse the model's reply as JSON ---
    try:
        return _extract_json(response.choices[0].message.content)
    except json.JSONDecodeError:
        # If the model didn't return valid JSON at all, fail safely instead of crashing.
        return {"verdict": "error", "issues": ["Model returned invalid JSON"]}


# ------------------------------------------------------------
# 4) TEST BLOCK — only runs when you execute this file directly
#    (python agents/this_file.py), NOT when another file imports it.
#    Lets you test one diff from the command line or a file.
# ------------------------------------------------------------
if __name__ == "__main__":

    if len(sys.argv) < 2:
        # No diff file was given as an argument — tell the user how to use this script
        print("Usage: python agents/this_file.py <path_to_diff.txt>")
        sys.exit(1)

    # Read the diff text from the file path given on the command line
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        diff = f.read()

    # Run the agent and print the result
    result = review_TEMPLATE(diff)
    print(result)
""" Note:
All the agents only needs the diff.txt file to run , EXCEPT the story_matching_agent it also needs the 
ticket.txt file to run."""