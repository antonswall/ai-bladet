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
import urllib.parse

CREDENTIALS_PATH = os.path.expanduser("~/.moltbot/credentials.json")
API_BASE = "https://www.moltbook.com/api/v1"
ISSUE_URL = "https://ai-bladet.pages.dev"
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOLTBOOK_OUTPUT_DIR = os.path.join(PROJECT_DIR, "pipeline", "output", "moltbook")


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
    except urllib.error.URLError as e:
        print(f"moltbook: network error: {e}", file=sys.stderr)
        return None


def api_get(path, query=None):
    creds = load_credentials()
    if not creds:
        return None
    url = f"{API_BASE}{path}"
    if query:
        url += "?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {creds['api_key']}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read())
    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        print(f"moltbook: GET failed: {exc}", file=sys.stderr)
        return None


def already_published(week):
    result = api_get("/search", {"q": f"AI-Bladet Vecka {week}", "type": "posts", "limit": 20})
    for item in (result or {}).get("results", []):
        author = (item.get("author") or {}).get("name")
        title = item.get("title", "")
        status = item.get("verification_status") or item.get("verificationStatus")
        if author == "lutra_ai" and f"Vecka {week}" in title and status == "verified":
            return item.get("id")
    return None


def save_response(week, label, data, post_id="unknown"):
    os.makedirs(MOLTBOOK_OUTPUT_DIR, exist_ok=True)
    path = os.path.join(MOLTBOOK_OUTPUT_DIR, f"2026-{week}-{post_id}-{label}.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
    print(f"moltbook: saved {label} response — {path}")
    return path


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


def _detect_operator(challenge: str) -> str:
    """Identifiera explicit operator. Fallback-gissning är förbjuden."""
    signal = re.sub(r"(.)\1+", r"\1", re.sub(r"[^a-z]", "", challenge.lower()))
    if any(op in signal for op in ("multiplies", "multipliedby", "multiplied", "product", "times")):
        return "multiply"
    if "howfar" in signal and ("persecond" in signal or "perhour" in signal):
        return "multiply"
    if any(op in signal for op in ("slowsby", "reduces", "loses", "removes")):
        return "subtract"
    if any(op in signal for op in ("spedsup", "speedsup", "accelerates", "acelerates", "gains", "increases", "increasesby")):
        return "add"
    if any(op in signal for op in ("combined", "total", "exerts")):
        return "sum"
    raise ValueError(f"okänd operator i verifieringsutmaningen: signal={signal[:80]}")


def _extract_number_tokens(challenge: str) -> list[tuple[int, int]]:
    """Extrahera number-words från tokens och splittrade adjacent tokens."""
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

    return sorted(numbers, key=lambda item: item[0])


def _extract_numbers_from_compact(challenge: str) -> list[int]:
    """Fallback för ord som splittrats över fler än två noise-tokens."""
    compact = re.sub(r"[^a-z]", "", challenge.lower())
    word_to_number = {
        "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
        "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
        "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
        "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
        "nineteen": 19, "ten": 10, "nine": 9, "eight": 8, "seven": 7,
        "six": 6, "five": 5, "four": 4, "three": 3, "two": 2,
        "one": 1, "zero": 0,
    }
    tens_words = {"twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"}
    unit_words = {"one", "two", "three", "four", "five", "six", "seven", "eight", "nine"}
    words = sorted(word_to_number, key=len, reverse=True)
    patterns = {
        word: re.compile("".join(f"{char}+" for char in word), re.IGNORECASE)
        for word in word_to_number
    }
    boundaries = (
        "meterspersecond", "meterpersecond", "centimeterspersecond", "centimeterpersecond",
        "kilometersperhour", "meters", "meter", "centimeters", "centimeter", "seconds",
        "second", "velocity", "speed", "multipliedby", "multiplied", "times", "product",
        "gains", "increasesby", "increases", "speedsup", "slowsby", "reduces", "loses",
        "combined", "total", "and", "what", "is", "the", "at", "per", "by", "after",
    )
    out = []
    i = 0
    while i < len(compact):
        matched = False
        for word in words:
            m = patterns[word].match(compact, i)
            if not m:
                continue
            after = compact[m.end():]
            if word in tens_words:
                for unit in sorted(unit_words, key=len, reverse=True):
                    um = patterns[unit].match(compact, m.end())
                    if um:
                        after_unit = compact[um.end():]
                        if not after_unit or any(after_unit.startswith(b) for b in boundaries):
                            out.append(word_to_number[word] + word_to_number[unit])
                            i = um.end()
                            matched = True
                            break
                if matched:
                    break
            if after and not any(after.startswith(b) for b in boundaries):
                continue
            out.append(word_to_number[word])
            i = m.end()
            matched = True
            break
        if not matched:
            i += 1
    return out


def _merge_number_phrases(numbers: list[tuple[int, int]]) -> list[int]:
    """Slå bara ihop tens+units när orden ligger intill varandra i texten."""
    merged = []
    index = 0
    tens = {20, 30, 40, 50, 60, 70, 80, 90}
    units = {1, 2, 3, 4, 5, 6, 7, 8, 9}
    while index < len(numbers):
        pos, value = numbers[index]
        if (
            value in tens
            and index + 1 < len(numbers)
            and numbers[index + 1][1] in units
            and numbers[index + 1][0] == pos + 1
        ):
            merged.append(value + numbers[index + 1][1])
            index += 2
        else:
            merged.append(value)
            index += 1
    return merged


def solve_challenge(challenge: str) -> float:
    """Lös Moltbooks obfuskerade textproblem deterministiskt."""
    token_numbers = _merge_number_phrases(_extract_number_tokens(challenge))
    compact_numbers = _extract_numbers_from_compact(challenge)
    if len(compact_numbers) > len(token_numbers):
        merged = compact_numbers
    elif len(compact_numbers) == len(token_numbers) and compact_numbers != token_numbers:
        merged = compact_numbers
    else:
        merged = token_numbers

    signal = re.sub(r"(.)\1+", r"\1", re.sub(r"[^a-z]", "", challenge.lower()))
    if "point" in signal and len(merged) >= 2:
        merged = [merged[0] + merged[1] / 10] + merged[2:]

    if len(merged) < 2:
        raise ValueError(f"för få operander i verifieringsutmaningen: {merged}")

    operator = _detect_operator(challenge)
    if operator == "multiply":
        return merged[0] * merged[1]
    if operator == "subtract":
        return merged[0] - merged[1]
    if operator == "add":
        return merged[0] + merged[1]
    if operator == "sum":
        return sum(merged)
    raise ValueError(f"ohanterad operator: {operator}")

def main():
    week = get_week_number()
    if not week:
        print("moltbook: could not determine week number — skipping", file=sys.stderr)
        return 1

    existing_post_id = already_published(week)
    if existing_post_id:
        print(f"moltbook: vecka {week} already published — {existing_post_id}")
        return 0

    # Fetch the page to get the lead story title
    title = f"AI-Bladet Vecka {week} — ny upplaga ute!"
    content = (
        f"📰 **AI-Bladet Vecka {week}** är ute!\n\n"
        f"Nyhetsbrevet om AI med svenskt perspektiv — autonomt kuraterat från 30+ källor.\n\n"
        f"🔗 {ISSUE_URL}\n\n"
        f"#AI #Sverige #Nyheter"
    )

    recovery_note = os.getenv("AI_BLADET_MOLTBOOK_RECOVERY_NOTE", "").strip()
    if recovery_note:
        content += f"\n\n{recovery_note}"

    result = api_post("/posts", {
        "submolt_name": "general",
        "title": title,
        "content": content,
    })
    if result and result.get("success"):
        post_id = result.get("post", {}).get("id", "?")
        save_response(week, "post", result, post_id)
        print(f"moltbook: post created — {post_id}")

        # Verify post (math challenge)
        verify = result.get("post", {}).get("verification", {})
        vcode = verify.get("verification_code")
        challenge = verify.get("challenge_text", "")

        if vcode and challenge:
            print(f"moltbook: challenge — {challenge}")

            try:
                answer = solve_challenge(challenge)
                print(f"moltbook: parsed answer — {answer:.2f}")
            except ValueError as exc:
                print(f"moltbook: verification parse FAILED: {exc}", file=sys.stderr)
                return 1

            verify_result = api_post("/verify", {
                "verification_code": vcode,
                "answer": f"{answer:.2f}",
            })
            if verify_result:
                save_response(week, "verify", verify_result, post_id)
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
