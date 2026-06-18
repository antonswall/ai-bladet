# AI-Bladet — Driftrunbook

Operativ manual för den autonoma söndagskörningen. Vad som händer automatiskt,
vad du gör när något går fel, och hur du kör manuellt.

## Hur det är kopplat

- **Schemaläggning:** Hermes-agenten *lutra* (INTE system-cron/GitHub Actions).
  Jobb "AI-Bladet söndag", `0 7 * * 0` (söndagar 07:00), `deliver=telegram`.
  Konfig: `~/.hermes/cron/jobs.json`. **Anton ändrar cron själv via lutra.**
- **Runner:** `pipeline/run_weekly.sh` (källa, versionshanterad). Hermes kör en kopia
  i `~/.hermes/scripts/ai-bladet-weekly.sh`.
  ⚠️ **Single source of truth:** håll Hermes-kopian som symlänk till repo:t så de
  aldrig driftar isär:
  ```bash
  ln -sf ~/ai-bladet/pipeline/run_weekly.sh ~/.hermes/scripts/ai-bladet-weekly.sh
  ```
- **Flöde:** preflight → pipeline (collect→dedup→score→research→images→write) →
  validering (max 3 försök, Sonnet-retry) → `node build.js` → `git commit && push`
  → Cloudflare Pages deployar `public/` → https://ai-bladet.pages.dev/
- **Loggar:** `pipeline/output/runner-ÅÅÅÅ-MM-DD_HHMM.log` + leverans till Telegram.

## Manuell körning

```bash
# Torrkörning — kör allt UTOM git push (bygger lokalt, deployar inte):
SKIP_GIT_PUSH=1 bash ~/ai-bladet/pipeline/run_weekly.sh

# Skarp körning (samma som cron gör):
bash ~/ai-bladet/pipeline/run_weekly.sh
```
⚠️ Skriver över `content/ÅÅÅÅ-VV.md` för innevarande vecka (write.py regenererar).
Vill du behålla en handtrimmad utgåva: ta en kopia först.

## Fel-lägen & åtgärder

### 1. Validering underkänd efter 3 försök
- **Vad händer:** INGEN deploy. Utkastet ligger kvar i `content/ÅÅÅÅ-VV.md`.
  Rapport till Telegram + `pipeline/output/validated/`.
- **Du gör:** läs senaste filen i `pipeline/output/validated/` (fält `validation.issues`,
  `pass_rate`). Rätta `content/-filen` för hand, eller kör om. Vanliga orsaker:
  hallucinerad siffra/citat, saknad SE/EU-vinkel, dubblett lead↔sektion.
- **Publicera manuellt efter fix:**
  ```bash
  cd ~/ai-bladet && node build.js && git add -A \
    && git commit -m "Vecka NN — manuell fix" && git push origin main
  ```

### 2. Claude/Sonnet (OpenRouter) nere
- **Symptom:** `write.py` loggar "OpenRouter/Sonnet error" / tomt svar → steget failar.
- **Du gör:** oftast övergående. Kör om senare samma dag (`bash run_weekly.sh`).
  Kvarstår det: kolla OpenRouter-status + saldo. Inget halvpublicerat — failar före build.

### 3. git push failar (nät/auth)
- **Vad händer:** build är klar och utgåvan är **committad lokalt** — inget tappat.
- **Du gör:** när nät/auth är tillbaka:
  ```bash
  cd ~/ai-bladet && git push origin main
  ```
  Cloudflare deployar på push. Auth = osxkeychain (datorn måste vara upplåst).

### 4. Preflight-stopp ("❌ PREFLIGHT: …")
- Saknad binär/dep/nyckel. Avbryter FÖRE pipeline (inget halvgjort). Åtgärda det
  som listas (t.ex. `pip install requests beautifulsoup4 lxml`, eller nyckel i
  `~/.hermes/.env`) och kör om.

### 5. Inget hände alls på söndag
- Datorn (Mac Mini) måste vara på + upplåst kl 07:00. Kolla lutra-jobbets
  `last_run_at`/`last_status` i `~/.hermes/cron/jobs.json` och Telegram-leveransen.

## Manuell innehållsgranskning (rekommenderat)
Sajten deployar utan mänsklig granskning. Kolla `ai-bladet.pages.dev` söndag fm:
rubriker, bild/rubrik-matchning, att inga konstiga siffror smugit sig in. Hittar du
fel → rätta `content/-filen` → `node build.js` → commit/push (se §1).
