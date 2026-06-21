#!/usr/bin/env python3
"""Post the latest AI-Bladet issue to Moltbook.

Anropas automatiskt av run_weekly.sh efter lyckad deploy.
Kräver: environ API_KEY från credentials.json, eller skickas som argument.
"""
import json
import os
import sys
import urllib.request
import urllib.error

CREDENTIALS_PATH = os.path.expanduser("~/.moltbot/credentials.json")
API_BASE = "https://www.moltbook.com/api/v1"
ISSUE_URL = "https://ai-bladet.pages.dev"


def load_credentials():
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"moltbook: credentials not found at {CREDENTIALS_PATH}", file=sys.stderr)
        return None
    with open(CREDENTIALS_PATH) as f:
        return json.load(f)


def api_post(path, data):
    creds = load_credentials()
    if not creds:
        return None
    headers = {
        "Authorization": f"Bearer {creds['api_key']}",
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode()
    req = urllib.request.Request(f"{API_BASE}{path}", data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"moltbook: HTTP {e.code}: {e.read().decode()}", file=sys.stderr)
        return None


def get_week_number():
    """Läs veckonumret från senaste content-filen."""
    content_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "content")
    try:
        files = sorted([f for f in os.listdir(content_dir) if f.endswith(".md") and f.startswith("20")])
        if not files:
            return None
        latest = files[-1]
        # content/2026-25.md → 25
        parts = latest.replace(".md", "").split("-")
        return parts[1] if len(parts) >= 2 else None
    except (FileNotFoundError, IndexError):
        return None


def main():
    week = get_week_number()
    if not week:
        print("moltbook: could not determine week number — skipping", file=sys.stderr)
        return 1

    # Fetch the page to get the lead story title
    title = f"AI-Bladet Vecka {week} — ny upplaga ute!"
    content = (
        f"📰 **AI-Bladet Vecka {week}** är ute!\n\n"
        f"Nyhetsbrevet om AI med svenskt perspektiv — autonomt kuraterat från 30+ källor.\n\n"
        f"🔗 {ISSUE_URL}\n\n"
        f"#AI #Sverige #Nyheter"
    )

    result = api_post("/posts", {
        "submolt_name": "general",
        "title": title,
        "content": content,
    })
    if result and result.get("success"):
        post_id = result.get("post", {}).get("id", "?")
        print(f"moltbook: post created — {post_id}")

        # Verify post (math challenge)
        verify = result.get("post", {}).get("verification", {})
        vcode = verify.get("verification_code")
        challenge = verify.get("challenge_text", "")

        if vcode and challenge:
            print(f"moltbook: verifying...")
            clean = challenge
            for ch in "[]()/^,|~-":
                clean = clean.replace(ch, " ")
            clean = " ".join(clean.split())
            # Collapse doubled letters in number words
            import re
            for word in ["twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety",
                         "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
                         "eighteen", "nineteen", "ten", "one", "two", "three", "four", "five", "six",
                         "seven", "eight", "nine", "hundred", "thousand", "point"]:
                pattern = "".join(f"{c}+" for c in word)
                clean = re.sub(pattern, word, clean, flags=re.IGNORECASE)

            # Find numbers and operator
            import re as re2
            nums = [float(x) for x in re2.findall(r'\d+\.?\d*', challenge)]

            # Determine operation from text
            lower = challenge.lower()
            if "total force" in lower or "total" in lower:
                answer = sum(nums)
            elif "pushes back" in lower or "adds" in lower or "exerts" in lower or "and another" in lower:
                answer = sum(nums) if nums else 0
            elif "slows by" in lower or "loses" in lower or "removes" in lower or "drag" in lower:
                answer = nums[0] - nums[1] if len(nums) >= 2 else nums[0]
            elif "snaps" in lower and "times" in lower:
                answer = nums[0] * nums[1] if len(nums) >= 2 else nums[0]
            elif "swims" in lower and ("accelerates" in lower or "gains" in lower):
                answer = nums[0] + nums[1] if len(nums) >= 2 else nums[0]
            else:
                answer = sum(nums) if nums else 0

            verify_result = api_post("/verify", {
                "verification_code": vcode,
                "answer": f"{answer:.2f}",
            })
            if verify_result and verify_result.get("success"):
                print(f"moltbook: verification OK — post published! 🦞")
            else:
                print(f"moltbook: verification FAILED (answer={answer:.2f}) — post pending", file=sys.stderr)
        return 0
    else:
        print("moltbook: failed to create post", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
