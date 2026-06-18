#!/bin/bash
# AI-Bladet — Weekly runner
# Körs av cron varje söndag. Auto-deployar vid godkänd validering.

set -euo pipefail
PROJECT_DIR="$HOME/ai-bladet"
PIPELINE_DIR="$PROJECT_DIR/pipeline"
LOG_FILE="$PROJECT_DIR/pipeline/output/runner-$(date +%Y-%m-%d_%H%M).log"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "══════════════════════════════════════"
echo "  AI-BLADET · Weekly Runner"
echo "  $(date '+%Y-%m-%d %H:%M')"
echo "══════════════════════════════════════"

# ── Steg 1: Pipeline ──────────────────────────────────────
echo ""
echo "📡 Pipeline startar..."

cd "$PIPELINE_DIR"

# Source env
if [ -f "$HOME/.hermes/.env" ]; then
    export $(grep -v '^#' "$HOME/.hermes/.env" | xargs)
fi
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
fi

# Kör pipeline (utan rm seen.db — vi vill minnas tidigare)
python collect.py || { echo "❌ collect failade"; exit 1; }
python dedup.py || { echo "❌ dedup failade"; exit 1; }
python score.py || { echo "❌ score failade"; exit 1; }
python research.py --limit 15 || { echo "❌ research failade"; exit 1; }
python images.py || { echo "❌ images failade"; exit 1; }
python write.py || { echo "❌ write failade"; exit 1; }

echo "✅ Pipeline klar"

# ── Steg 2: Validering + Retry-loop ──────────────────────────
echo ""
echo "🔍 Validerar (max 3 försök)..."

MAX_RETRIES=3
ATTEMPT=0
VALIDATE_EXIT=1

while [ "$ATTEMPT" -lt "$MAX_RETRIES" ]; do
    ATTEMPT=$((ATTEMPT + 1))
    echo ""
    echo "  ── Försök $ATTEMPT/$MAX_RETRIES ──"

    python validate.py
    VALIDATE_EXIT=$?

    # Hämta resultat
    WEEK=$(ls -t "$PIPELINE_DIR/output/validated/"*.json 2>/dev/null | head -1)
    if [ -f "$WEEK" ]; then
        WEEK_STEM=$(basename "$WEEK" .json)
        WEEK_NUM=$(python3 -c "import json; d=json.load(open('$WEEK')); print(d['frontmatter'].get('week','?'))" 2>/dev/null || echo "?")
        PASS_RATE=$(python3 -c "import json; d=json.load(open('$WEEK')); print(f\"{d['meta']['pass_rate']*100:.0f}%\")" 2>/dev/null || echo "?")
        ISSUE_COUNT=$(python3 -c "import json; d=json.load(open('$WEEK')); print(d['meta']['issue_count'])" 2>/dev/null || echo "?")

        # Kolla hårda checks
        DUP_FAIL=$(python3 -c "import json; d=json.load(open('$WEEK')); print('FAIL' if d.get('validation',{}).get('duplication',{}).get('duplicate') else '')" 2>/dev/null)
        SE_FAIL=$(python3 -c "import json; d=json.load(open('$WEEK')); print('FAIL' if not d.get('validation',{}).get('se_eu_angle',{}).get('found') else '')" 2>/dev/null)
    else
        PASS_RATE="?"
        ISSUE_COUNT="?"
        DUP_FAIL=""
        SE_FAIL=""
    fi

    if [ "$VALIDATE_EXIT" -eq 0 ]; then
        echo "✅ Validering PASS ($PASS_RATE, $ISSUE_COUNT issues)"
        break
    fi

    # FAIL — bygg feedback för retry
    echo "❌ Validering FAIL ($PASS_RATE, $ISSUE_COUNT issues) — försök $ATTEMPT/$MAX_RETRIES"

    FEEDBACK=""
    if [ -f "$WEEK" ]; then
        FEEDBACK=$(python3 -c "
import json
d=json.load(open('$WEEK'))
issues = d.get('validation',{}).get('issues',[])
dup = d.get('validation',{}).get('duplication',{})

lines = []
if dup.get('duplicate'):
    lines.append(f'DUBBLETT: {dup.get(\"reason\",\"\")}')

# Lägg till SE/EU fail
if not d.get('validation',{}).get('se_eu_angle',{}).get('found'):
    lines.append('SE/EU-VINKEL SAKNAS: Minst en story måste ha svensk eller EU-vinkel.')

# Lägg till high/medium issues
for i in issues:
    sev = i.get('severity','')
    if sev in ('high','medium'):
        lines.append(f'[{sev.upper()}] {i.get(\"location\",\"?\")}: {i.get(\"claim\",\"\")}\n  Problem: {i.get(\"problem\",\"\")}')

print(chr(10).join(lines[:8]))
" 2>/dev/null)
    else
        FEEDBACK="Validering returnerade inget resultat. Kontrollera pipeline-output."
    fi

    if [ -z "$FEEDBACK" ]; then
        FEEDBACK="Valideringsfel utan specifika issues. Kör om med striktare källkoll."
    fi

    # Retry med feedback
    if [ "$ATTEMPT" -lt "$MAX_RETRIES" ]; then
        echo ""
        echo "  🔄 Retry: skickar feedback till Sonnet..."
        python write.py --feedback "$FEEDBACK" || { echo "❌ write.py failade under retry"; break; }
    fi
done

# ── Steg 3: Beslut ────────────────────────────────────────
if [ "$VALIDATE_EXIT" -eq 0 ]; then
    echo ""
    echo "✅ Validering GODKÄND efter $ATTEMPT försök"

    # Bygg site
    echo ""
    echo "🔨 Bygger site..."
    cd "$PROJECT_DIR"
    node build.js || { echo "❌ build failade"; exit 1; }

    if [ -z "${SKIP_GIT_PUSH:-}" ]; then
        echo ""
        echo "📤 Pushar till GitHub..."
        git add -A
        git commit -m "Vecka ${WEEK_NUM:-$(date +%W)} · $(date +%Y-%m-%d) — auto" || true
        git push origin main || { echo "❌ git push failade"; exit 1; }

        echo ""
        echo "══════════════════════════════════════"
        echo "  🚀 DEPLOYAD till ai-bladet.pages.dev"
    else
        echo ""
        echo "══════════════════════════════════════"
        echo "  ✅ TESTKÖRNING — ingen push (SKIP_GIT_PUSH satt)"
    fi
    echo "  Vecka: ${WEEK_NUM:-$(date +%W)}"
    echo "  Validering: $PASS_RATE pass-rate"
    echo "  Issues: $ISSUE_COUNT"
    echo "  Försök: $ATTEMPT"
    echo "══════════════════════════════════════"

else
    echo ""
    echo "══════════════════════════════════════"
    echo "  ⛔ INGEN DEPLOY — validering underkänd efter $MAX_RETRIES försök"
    echo "  Vecka: ${WEEK_NUM:-$(date +%W)}"
    echo "  Pass-rate: $PASS_RATE (tröskel: 70%)"
    echo "  Issues: $ISSUE_COUNT"
    echo ""
    echo "  📄 Full rapport: pipeline/output/validated/"
    echo "  📄 Utkast: content/${WEEK_STEM:-vecka-okänd}.md"
    echo "══════════════════════════════════════"

    exit 1
fi
