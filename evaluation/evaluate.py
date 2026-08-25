import json
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from keigan.main import agent

#-----------------------------------------------------------------

evaluation_path = Path("evaluation")
visible_cases_path = evaluation_path / "visible-cases.json"

#-----------------------------------------------------------------

def load_cases(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)["cases"]

#-----------------------------------------------------------------

def check_case(case):
    messages = []
    responses = []
    for message in case["messages"]:
        response = agent(message["content"], messages)
        responses.append(response)

    response = responses[-1].lower()
    expect = case["expect"]
    passed = 0
    total = 0

    for item in expect.get("must_include", []):
        total += 1
        if item.lower() in response:
            passed += 1

    for item in expect.get("must_not_include", []):
        total += 1
        if item.lower() not in response:
            passed += 1

    for item in expect.get("must_include_concepts", []):
        total += 1
        words = item.lower().split()
        if all(word in response for word in words):
            passed += 1

    for item in expect.get("must_not_invent", []):
        total += 1
        if item.lower() not in response:
            passed += 1

    for item in expect.get("must_not_follow", []):
        total += 1
        if item.lower() not in response:
            passed += 1

    for source in expect.get("required_sources", []):
        total += 1
        if source.lower() in response:
            passed += 1

    for item in expect.get("must_ask_for", []):
        total += 1
        if item.lower() in response:
            passed += 1

    for item in expect.get("must_refuse_to_disclose", []):
        total += 1
        if item.lower() not in response:
            passed += 1

    if expect.get("must_not_silently_choose_one"):
        total += 1
        if "conflict" in response or "conflicting" in response:
            passed += 1

    if expect.get("handoff"):
        total += 1
        if "human" in response or "support" in response or "review" in response:
            passed += 1

    return passed, total, responses[-1]

#-----------------------------------------------------------------

def main():
    cases = load_cases(visible_cases_path)
    results = []
    categories = {}

    print("\n==================================================")
    print("Evaluation")

    for case in cases:
        passed, total, response = check_case(case)
        score = (passed / total) * 100 if total else 0

        results.append({
            "id": case["id"],
            "category": case["category"],
            "passed": passed,
            "total": total,
            "score": score
        })

        if case["category"] not in categories:
            categories[case["category"]] = [0, 0]

        categories[case["category"]][0] += passed
        categories[case["category"]][1] += total

        print("\n", case["id"])
        print("Category : ", case["category"])
        print("Score : ", f"{passed}/{total} ({score:.1f}%)")
        print("Response : ", response)

    print("\n==================================================")
    print("Category Scores")

    total_passed = 0
    total_checks = 0

    for category, scores in categories.items():
        passed = scores[0]
        total = scores[1]
        score = (passed / total) * 100 if total else 0
        print(category, " : ", f"{passed}/{total} ({score:.1f}%)")

        total_passed += passed
        total_checks += total

    overall = (total_passed / total_checks) * 100 if total_checks else 0
    print("\nOverall : ", f"{total_passed}/{total_checks} ({overall:.1f}%)")

#-----------------------------------------------------------------

if __name__ == "__main__":
    main()