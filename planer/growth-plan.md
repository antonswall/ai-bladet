# AI-Bladet — Tillväxtplan: Sveriges största AI-publikation

Version: 1.0 · Datum: 2026-07-11 · Ägare: Anton · Exekvering: Lutra + Anton (3–5 h/v)

---

## 0. Läsinstruktion för Lutra

- Detta är masterplanen. Bryt ner varje F-uppgift till subtasks i vaulten innan kodning.
- [BESLUT ANTON] = kräver Antons godkännande innan exekvering. Skicka via Telegram, en fråga i taget.
- Rör aldrig befintlig publiceringspipeline utan validering i staging först.
- Scope-disciplin enligt SOUL.md gäller: en sak i taget.

---

## 1. Mål & ramar

Vision: Sveriges största AI-fokuserade publikation, mätt i (a) e-postprenumeranter, (b) organisk sajttrafik/månad, (c) betalande prenumeranter — jämfört med svenska publikationer med AI som huvudämne.

Positionering: "Veckans viktigaste AI-nyheter, översatta till affärskonsekvens för svenska beslutsfattare. 5 minuter, noll hype."

Kärnläsare: Beslutsfattare i svenska företag (VD, CTO, digitaliseringsansvarig, mellanchef med AI-mandat). Sekundärt: konsulter/rådgivare som säljer till dessa.

Hårda ramar:
- 100% organisk tillväxt. Inga betalda annonser (Google/Meta/LinkedIn Ads) innan ≥3 betalande kunder finns.
- Antons manuella tid: max 3–5 h/vecka. Lutra eskalerar aldrig scope utöver detta utan beslut.
- Anton agerar kurator under eget namn (professionell roll, aldrig privatperson). Full personvarumärkes-satsning omprövas vid 300 free-prenumeranter.
- All kod skrivs av AI. Anton orkestrerar och beslutar.
- E-postlistan är tillgången. Alla kanaler driver dit.

---

## 2. KPI:er & milstolpar

Tidpunkt | Free | Betalande | Övrigt
---|---|---|---
Dec 2026 (baseline) | 50 | 3 | Öppningsgrad ≥45%
Jun 2027 (baseline) | 200 | 15–20 | ≥1 000 organiska besök/mån
Dec 2027 (stretch) | 1 000 | 50 | ≥1 nationell medieomnämning
Dec 2028 (vision) | 5 000+ | 200+ | Störst i nischen

Veckometrik (Lutra spårar): nya prenumeranter per källa, churn, öppningsgrad, klickfrekvens, sajtbesök per källa, LinkedIn-räckvidd/följare, topp-3 innehåll.

---

## 3. Fas 0 — Fundament (vecka 1–2)

ID | Uppgift | Ansvar | Acceptanskriterier
---|---|---|---
F0-1 | Publikt arkiv med SEO. Varje nummer = egen URL på sajten. | Lutra | Unik title/meta per sida, schema.org Article, sitemap.xml, intern länkning mellan nummer, Lighthouse SEO ≥95
F0-2 | Programmatisk SEO: svensk AI-ordlista. 60 termer (RAG, MCP, agenter, embeddings, kontextfönster, tokens, finetuning, evals …). | Lutra | 300–600 ord/term på svenska, affärsvinkel + konkret exempel, interlänkade, CTA till prenumeration. Publicera 5/vecka, inte allt på en gång
F0-3 | LinkedIn-utkastgenerator i pipelinen. Nytt pipeline-steg efter write. | Lutra | 3 utkast/nummer i 3 format (nyhetsanalys, lista, kontrarisk take). Svenska, 800–1 300 tecken, hook på rad 1, CTA på sista raden. Levereras till Telegram för Antons polering
F0-4 | LinkedIn-närvaro. Företagssida + LinkedIn Newsletter som spegel av veckobrevet. | Anton (setup) + Lutra (innehåll) | Spegel publiceras <24 h efter e-postutskick. LinkedIn Newsletter pushar notiser till följare = gratis distribution
F0-5 | Analytics. Plausible (självhostad i homelab-stacken) eller CF Web Analytics + UTM-standard. | Lutra | Källspårning på alla kanaler, automatiserad veckorapport
F0-6 | Konverteringsoptimering. Signup-flöde + välkomstmejl. | Lutra | Signup ≤2 fält, social proof + "5 min/vecka för beslutsfattare" på landningssidan, välkomstmejl med bästa tidigare innehåll skickas <5 min
F0-7 | Delningskort. Auto-genererade OG-bilder per nummer och ordlisteterm. | Lutra | Korrekt preview-rendering på LinkedIn och X
F0-8 | Referral-grund. Unik referral-länk per prenumerant (aktiveras Fas 2). | Lutra | Spårning fungerar end-to-end i testmiljö

---

## 4. Fas 1 — 0→100 free (månad 1–3)

Antons veckoloop (3–5 h, detta är taket)

Dag | Tid | Aktivitet
---|---|---
Mån | 30 min | Polera + schemalägg veckans 3 LinkedIn-inlägg (Lutras utkast, F0-3)
Tis/ons/tors | 3 × 20 min | Kommentera substantiellt hos 5 svenska AI-profiler/företagsledare per pass
Fre | 45 min | 5–10 personliga DM enligt playbook nedan
Valfri | 60 min | Veckans experiment

DM-playbook (värde först)

1. Målgrupp: personer som nyligen postat/kommenterat om AI i sin verksamhet.
2. Format: 1 konkret insikt kopplad till deras inlägg + "Jag sammanfattar det här varje vecka för svenska beslutsfattare — vill du ha nästa nummer?"
3. Regler: aldrig massutskick, max 10/vecka (spamrisk), alltid manuellt av Anton, logga utfall i vaulten.

Lutra-stöd Fas 1

ID | Uppgift | Kriterier
---|---|---
F1-1 | Prospektlista: föreslå 15 DM-kandidater/vecka via bevakning av publika källor | Inga inloggade LinkedIn-scrapes (ToS). Namn + kontext + föreslagen öppningsrad
F1-2 | Cross-promo-research: kartlägg 10 svenska nyhetsbrev (start: Birgir Birgissons veckobrev) | Kontaktväg + skräddarsydd pitch per brev. [BESLUT ANTON] innan utskick
F1-3 | Innehållsåtervinning: varje nummer → 1 SEO-artikel "veckans analys" på sajten | Publiceras automatiskt, interlänkad med arkiv + ordlista

Gate till Fas 2: ≥100 free ELLER 3 månader passerat → utvärdering.

---

## 5. Fas 2 — 100→300 + premium (månad 3–6)

Premium-lansering (gate: ≥150 free)

- Pris [BESLUT ANTON]: förslag 79–99 kr/mån eller 790 kr/år.
- Free = veckobrevet. Paid = 1 djupanalys/månad + svensk AI-verktygsdatabas + fullt arkiv + [BESLUT ANTON: ev. mer].
- Lanseringssekvens: 3 mejl — (1) avisering, (2) lansering med founding member-rabatt 30% livstid för första 20, (3) sista chansen.
- Förväntad konvertering: 2–5% av engagerade free. Räkna inte med mer.

Uppgifter

ID | Uppgift | Kriterier
---|---|---
F2-1 | Referralprogram live (bygger på F0-8): 3 värvningar = 1 månad premium | Automatisk kreditering, synlig räknare i mejlfooter
F2-2 | Poddoutreach: lista 10 svenska tech-/affärspoddar med pitch "21-åring driver helautomatiserad AI-tidning" | [BESLUT ANTON] per pitch
F2-3 | SEO-iteration: analysera sökdata, dubblera ned på termer med visningar, +20 nya sidor | Datadrivet urval, rapport i månadsrapporten
F2-4 | Betalflöde: Stripe Checkout + kvitto + medlemsåtkomst | Köp→åtkomst <2 min, churn-mejl automatiserat

Gate till Fas 3: ≥250 free + ≥5 betalande.

---

## 6. Fas 3 — 300→1 000+ (månad 6–12)

PR-offensiven (störst hävstång i hela planen)

ID | Uppgift | Detalj
---|---|---
F3-1 | Pressmaterial | Pressmeddelande, faktablad, bilder, "om"-sida. Lutra producerar, Anton godkänner
F3-2 | Pitchlista | Breakit, DI Digital, Ny Teknik, Computer Sweden, NA (lokalvinkel Örebro). Vinklar: (a) 21-åring i Örebro driver helautomatiserad nyhetstidning, (b) "AI skriver om AI — och beslutsfattarna läser", (c) soloperson + agentstack. [BESLUT ANTON] på allt utgående
F3-3 | Partnerskap | AI Swedens community (My AI, 27 000+ medlemmar), Handelskammaren Mälardalen, Örebro universitet/AASS-nätverket, lokala näringslivsfrukostar — Anton talar 1 ggr/kvartal om AI för företag
F3-4 | Webinar/LinkedIn Live 1×/kvartal | "AI-läget för svenska företag — Q&A". Lutra producerar underlag, Anton levererar 30 min
F3-5 | Omprövning personvarumärke | Vid 300 free: beslut om full personlig LinkedIn-satsning

Gate till Fas 4: ≥1 000 free + ≥30 betalande + ≥1 nationell medieomnämning.

---

## 7. Fas 4 — Dominans (år 2+)

- Sponsorintäkter (organisk-kompatibelt): 1 sponsor/nummer, svensk B2B-SaaS. Från ~2 500 kr/nummer vid 1 000+ prenumeranter. [BESLUT ANTON]
- Företagsprenumeration: team-licenser (5+ säten) till SMB.
- Segmentering: branschutgåvor (t.ex. bygg — Pilotage-domänkunskap finns) om data visar efterfrågan.
- Bemanning: frilans-kurator endast om det inte bryter Bana A-ramarna (frihet > pengar > status).
- Definiera segern publikt: störst bland AI-fokuserade svenska publikationer; jämför öppet mot etablerade aktörers AI-bevakning.

---

## 8. Mätning & rapportering (Lutra)

Veckorapport (söndag 18:00, Telegram):
1. KPI-tabell vs mål
2. Källfördelning nya prenumeranter
3. Bästa/sämsta innehåll (öppning + klick)
4. LinkedIn: räckvidd, följare, bästa inlägg
5. SEO: visningar, klick, nya rankade termer
6. Exakt 1 rekommenderad åtgärd nästa vecka

Månadsrapport: trendanalys + gate-status + experimentutfall.

---

## 9. Beslutsgrindar

Trigger | Åtgärd
---|---
150 free | Lansera premium
300 free | Ompröva personvarumärke fullt ut
3 betalande | Betalda annonser tillåtna (ej krav)
250 free + 5 paid | Starta PR-offensiv (Fas 3)
Öppningsgrad <35% två veckor i rad | Innehålls-audit, pausa tillväxtexperiment
1 000 free | Öppna sponsorförsäljning

---

## 10. Experimentbacklog (1/vecka, prioriterad)

1. A/B: ämnesrader (nyfikenhet vs konkret nytta)
2. LinkedIn-format: karusell/PDF vs textinlägg
3. "Fråga AI-bladet" — läsarfrågor besvaras i brevet (engagemang + innehåll gratis)
4. Svensk AI-verktygsdatabas som lead magnet
5. Kvartalsrapport "AI i svenska företag" (egen enkätdata) → PR + inlänkar
6. X/Twitter-spegel (Lutra automatiserar, låg kostnad)
7. Reddit/svenska forum — endast värdeinlägg, aldrig länkspam
8. Gästartikel i branschmedia

---

## 11. Risker & motdrag

Risk | Motdrag
---|---
Svag LinkedIn-räckvidd utan personprofil | Kurator-roll + kommentarsstrategi bär Fas 1; ompröva vid 300 free
"AI-genererat" = förtroendeproblem hos beslutsfattare | Full transparens som USP: "byggd med AI, kuraterad av människa"
Spamflagg vid DM-outreach | Max 10/v, alltid manuellt och personligt, logga allt
SEO tar 4–6 mån att ge effekt | Förväntanshantering: LinkedIn bär Fas 1, SEO bär Fas 2–3
Antons tid överskrids | Veckoloopen är taket; Lutra flaggar, aldrig utökar
Plattformsberoende (algoritmändringar) | E-postlistan är tillgången; allt driver dit

---

## 12. Omedelbar nästa åtgärd

F0-1 (publikt arkiv med SEO). Lutra: bekräfta mottagen plan, returnera nedbrytning av F0-1 i subtasks + tidsestimat innan kodning startar.
