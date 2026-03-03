import os
import sys
from openai import OpenAI

token = os.environ.get("GITHUB_TOKEN")
if not token:
    print("ERROR: GITHUB_TOKEN not set", file=sys.stderr)
    sys.exit(1)

with open("pr.diff") as f:
    diff = f.read()

if not diff.strip():
    summary = "No changes detected in this PR."
    with open("review_output.md", "w") as f:
        f.write(f"## AI Code Review\n\n{summary}\n\n**Verdict: PASS**")
    sys.exit(0)

client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=token,
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "system",
            "content": (
                "You are a strict security-focused code reviewer. "
                "Review the PR diff and respond using EXACTLY this format:\n\n"
                "**Risk level:** LOW | MEDIUM | HIGH\n\n"
                "**Findings:**\n"
                "- List each issue with file, description, and severity\n"
                "- Write 'None' if no issues found\n\n"
                "**Required actions:**\n"
                "- List blocking issues that must be fixed before merge\n"
                "- Write 'None' if no blockers\n\n"
                "**Suggestions:**\n"
                "- List non-blocking improvements\n"
                "- Write 'None' if no suggestions\n\n"
                "**Verdict:** PASS | FAIL\n\n"
                "Use FAIL if there are any hardcoded secrets, backdoors, "
                "disabled security controls, or critical bugs."
            ),
        },
        {
            "role": "user",
            "content": f"Review this PR diff:\n\n```diff\n{diff}\n```",
        },
    ],
)

review = response.choices[0].message.content

with open("review_output.md", "w") as f:
    f.write(f"## AI Code Review\n\n{review}\n")

verdict_is_fail = "**Verdict:** FAIL" in review or "**verdict:** fail" in review.lower()

if verdict_is_fail:
    print("AI review returned FAIL — blocking merge.", file=sys.stderr)
    sys.exit(1)

print("AI review passed.")
sys.exit(0)
