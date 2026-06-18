# AGENTS.md — Samarbetskontrakt för AI-Bladet

Två agenter turas om att jobba i detta projekt. **`loggbok.md` är den delade
minnesboken** — den här filen säger hur ni använder den så ni alltid ser vad den
andra gjort.

## Vilka jobbar här
- **Claude Code** — körs på Antons dator. Kodar, designar, bygger, committar, pushar.
  Rör **ALDRIG** `~/.hermes/` (läs-koll ok, men ändra/skapa inget där).
- **lutra** (Hermes-agent) — äger schemaläggning (cron i `~/.hermes/`) och kör
  söndagspipelinen. Sköter allt under `~/.hermes/` själv.

## Rutin — varje gång, oavsett vem du är
1. **INNAN** du börjar: läs de översta posterna i `loggbok.md` (vad hände sist?),
   och `RUNBOOK.md` om det gäller drift.
2. Gör jobbet.
3. **NÄR** du är klar: lägg en kort post **högst upp** i `loggbok.md`:
   ```
   ## ÅÅÅÅ-MM-DD — [vem] Kort titel
   - vad du ändrade (filer / varför)
   - vad den andra behöver veta / nästa steg
   ```
   Tagga `[vem]`: **`[Claude Code]`** eller **`[lutra]`**.
4. **Claude Code:** committa + pusha (loggboken ingår i commiten).
   **lutra:** läs in ändringen i ditt minne.

## Revirgränser
- Schemaläggning / cron / allt i `~/.hermes/` → **lutra**. Claude Code föreslår,
  rör inte.
- Sajtkod, pipeline-källkod, `content/`, design → endera agenten, men **logga alltid**.
- Single source of truth för runnern: `~/.hermes/scripts/ai-bladet-weekly.sh` är en
  **symlänk** till `pipeline/run_weekly.sh` (så ändringar i repot når söndagsjobbet).

## Snabborientering
- **Bygg:** `node build.js` → `public/` → Cloudflare deployar vid push till `main`.
- **Autonomi:** lutra-cron "AI-Bladet söndag" `0 7 * * 0` → `run_weekly.sh`.
- **Historik & beslut:** `loggbok.md`. **Drift & felhantering:** `RUNBOOK.md`.
