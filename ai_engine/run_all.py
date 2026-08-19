import os
os.environ["LITELLM_LOG"] = "ERROR"

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Make sure Python can find the agent modules inside agents/
sys.path.insert(0, os.path.dirname(__file__))

try:
    from ai_engine.agents.security_agent import review_security
    from ai_engine.agents.performance_agent import review_performance
    from ai_engine.agents.story_match_agent import review_story_match
    from ai_engine.agents.tech_debt_agent import review_tech_debt
except ImportError:
    from agents.security_agent import review_security
    from agents.performance_agent import review_performance
    from agents.story_match_agent import review_story_match
    from agents.tech_debt_agent import review_tech_debt


def main():
    if len(sys.argv) < 3:
        print("Usage: python run_all.py <path_to_diff.txt> <path_to_ticket.txt>")
        sys.exit(1)

    diff_path = sys.argv[1]
    ticket_path = sys.argv[2]

    with open(diff_path, "r", encoding="utf-8") as f:
        diff = f.read()
    with open(ticket_path, "r", encoding="utf-8") as f:
        ticket = f.read()

    # Map agent name -> callable that takes only diff (story_match needs ticket too)
    jobs = {
        "security": lambda: review_security(diff),
        "performance": lambda: review_performance(diff),
        "story_match": lambda: review_story_match(diff, ticket),
        "tech_debt": lambda: review_tech_debt(diff),
    }

    print(f"Running {len(jobs)} agents in parallel...\n")
    start = time.time()

    results = {}
    with ThreadPoolExecutor(max_workers=len(jobs)) as executor:
        future_to_name = {executor.submit(fn): name for name, fn in jobs.items()}
        for future in as_completed(future_to_name):
            name = future_to_name[future]
            try:
                results[name] = future.result()
            except Exception as e:
                results[name] = {"verdict": "error", "issues": [f"Runner failed: {e}"]}

    elapsed = time.time() - start

    print("=" * 60)
    print(f"ALL AGENTS COMPLETE  ({elapsed:.1f}s total)")
    print("=" * 60)

    # Print in a fixed, predictable order regardless of completion order
    for name in ["security", "performance", "story_match", "tech_debt"]:
        result = results[name]
        verdict = result.get("verdict", "unknown").upper()
        print(f"\n[{name.upper()}] -> {verdict}")
        for issue in result.get("issues", []):
            print(f"  - {issue}")

    print("\n" + "=" * 60)

    # Overall summary line, handy for a demo screen
    overall = "PASS" if all(r.get("verdict") == "pass" for r in results.values()) else "FAIL"
    print(f"OVERALL VERDICT: {overall}")


if __name__ == "__main__":
    main()