#!/usr/bin/env python3
"""Post the latest AI-Bladet issue to Moltbook.

Anropas automatiskt av run_weekly.sh efter lyckad deploy.
Kräver: environ API_KEY från credentials.json, eller skickas som argument.
"""
import json
import os
import re
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


def solve_challenge(challenge: str) -> int:
    """Lös Moltbooks obfuskerade textproblem deterministiskt."""
    spaced = re.sub(r"[^a-zA-Z\s]", " ", challenge)
    tokens = [token for token in spaced.split() if token]
    word_to_number = {
        "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
        "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
        "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
        "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
        "nineteen": 19, "ten": 10, "nine": 9, "eight": 8, "seven": 7,
        "six": 6, "five": 5, "four": 4, "three": 3, "two": 2,
        "one": 1, "zero": 0, "hundred": 100, "thousand": 1000,
    }
    patterns = {
        word: re.compile("".join(f"{char}+" for char in word), re.IGNORECASE)
        for word in word_to_number
    }
    sorted_words = sorted(word_to_number, key=len, reverse=True)
    used = set()
    numbers = []

    for index, token in enumerate(tokens):
        for word in sorted_words:
            if patterns[word].fullmatch(token):
                used.add(index)
                numbers.append((index, word_to_number[word]))
                break

    for index in range(len(tokens) - 1):
        if index in used or index + 1 in used:
            continue
        if len(tokens[index]) <= 2 and len(tokens[index + 1]) <= 2:
            continue
        combined = tokens[index] + tokens[index + 1]
        for word in sorted_words:
            if patterns[word].fullmatch(combined):
                used.update((index, index + 1))
                numbers.append((index, word_to_number[word]))
                break

    numbers.sort(key=lambda item: item[0])
    values = [value for _, value in numbers]
    merged = []
    index = 0
    tens = {20, 30, 40, 50, 60, 70, 80, 90}
    units = {1, 2, 3, 4, 5, 6, 7, 8, 9}
    while index < len(values):
        value = values[index]
        if value in tens and index + 1 < len(values) and values[index + 1] in units:
            merged.append(value + values[index + 1])
            index += 2
        else:
            merged.append(value)
            index += 1

    if not merged:
        raise ValueError("inga tal hittades i verifieringsutmaningen")

    signal = re.sub(r"(.)\1+", r"\1", re.sub(r"[^a-z]", "", challenge.lower()))
    if "multiplies" in signal or "product" in signal or "times" in signal:
        if len(merged) < 2:
            raise ValueError("multiplikation saknar två tal")
        return merged[0] * merged[1]
    if "slowsby" in signal or "reduces" in signal or "loses" in signal or "removes" in signal:
        return merged[0] - merged[1] if len(merged) >= 2 else merged[0]
    if "speedsup" in signal or "accelerates" in signal or "gains" in signal:
        return merged[0] + merged[1] if len(merged) >= 2 else merged[0]
    return sum(merged)


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

            try:
                answer = solve_challenge(challenge)
            except ValueError as exc:
                print(f"moltbook: verification parse FAILED: {exc}", file=sys.stderr)
                return 1

            verify_result = api_post("/verify", {
                "verification_code": vcode,
                "answer": f"{answer:.2f}",
            })
            if verify_result and verify_result.get("success"):
                print(f"moltbook: verification OK — post published! 🦞")
            else:
                print(f"moltbook: verification FAILED (answer={answer:.2f}) — post pending", file=sys.stderr)
                return 1
        return 0
    else:
        print("moltbook: failed to create post", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
