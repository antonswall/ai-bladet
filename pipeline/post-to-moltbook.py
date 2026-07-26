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

            # Moltbook obfuskerar: symboler + case-förvirring + dubblerade bokstäver +
            # sifferord sönderdelade över tokens (tWwEeN tYy = "twenty").
            # Strategi: behåll ordgränser (ersätt symboler med space), sen token+pair-matching.

            import re

            # Steg 1: tokens
            spaced = re.sub(r'[^a-zA-Z\s]', ' ', challenge)
            tokens = [t for t in spaced.split() if t]

            w2n = {
                "twenty":20,"thirty":30,"forty":40,"fifty":50,"sixty":60,"seventy":70,"eighty":80,"ninety":90,
                "eleven":11,"twelve":12,"thirteen":13,"fourteen":14,"fifteen":15,"sixteen":16,"seventeen":17,
                "eighteen":18,"nineteen":19,"ten":10,"nine":9,"eight":8,"seven":7,"six":6,"five":5,
                "four":4,"three":3,"two":2,"one":1,"zero":0,"hundred":100,"thousand":1000,
            }
            pats = {w: re.compile("".join(f"{c}+" for c in w), re.IGNORECASE) for w in w2n}
            sw = sorted(w2n.keys(), key=len, reverse=True)

            used = set()
            numbers = []

            # Pass 1: individuella tokens
            for i, tok in enumerate(tokens):
                for w in sw:
                    if pats[w].fullmatch(tok):
                        used.add(i)
                        numbers.append((i, w2n[w]))
                        break

            # Pass 2: par (i, i+1) — hoppa om båda tokens ≤2 chars (false positive-risk)
            i = 0
            while i < len(tokens) - 1:
                if i not in used and (i+1) not in used:
                    if len(tokens[i]) <= 2 and len(tokens[i+1]) <= 2:
                        i += 1
                        continue
                    comb = tokens[i] + tokens[i+1]
                    for w in sw:
                        m = pats[w].match(comb)
                        if m and m.end() == len(comb):
                            used.add(i); used.add(i+1)
                            numbers.append((i, w2n[w]))
                            break
                i += 1

            # Sortera efter token-index och extrahera values
            numbers.sort(key=lambda x: x[0])
            values = [v for _, v in numbers]

            # Merge tens+units: t.ex. [20, 4] → [24]
            merged = []
            i = 0
            tens = [20,30,40,50,60,70,80,90]
            units = [1,2,3,4,5,6,7,8,9]
            while i < len(values):
                v = values[i]
                if v in tens and i+1 < len(values) and values[i+1] in units:
                    merged.append(v + values[i+1])
                    i += 2
                else:
                    merged.append(v)
                    i += 1

            # Operator detection: kollapsa dubletter för att hantera "speeeedsup" → "speedsup"
            sig = re.sub(r'(.)\1+', r'\1', re.sub(r'[^a-z]', '', challenge.lower()))
            if "speedsup" in sig or "accelerates" in sig or "gains" in sig:
                answer = merged[0] + merged[1] if len(merged) >= 2 else merged[0]
            elif "slowsby" in sig:
                answer = merged[0] - merged[1] if len(merged) >= 2 else merged[0]
            elif "reduces" in sig or "loses" in sig or "removes" in sig:
                answer = merged[0] - merged[1] if len(merged) >= 2 else merged[0]
            elif "combined" in sig or "total" in sig or "exerts" in sig:
                answer = sum(merged) if merged else 0
            else:
                answer = sum(merged) if merged else 0

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
