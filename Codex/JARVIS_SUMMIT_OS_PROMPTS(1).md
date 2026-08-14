# JARVIS × SUMMIT OS — Master Prompt Package

**How to use this file:** Do the prep checklist first. Then paste each prompt into Claude Code *one at a time*, in order. Wait for each to finish and test before moving on. Do not paste them all at once — that is the single fastest way to get a half-built system.

**Model:** Select your most capable model in Claude Code for Prompts 0, 1, and 6 (the architecture, ingestion, and audit work). Prompts 2–5 are implementation and run fine on a standard model.

---

## PREP — do this before you touch Claude Code

- [ ] **Export your Claude history.** claude.ai → your initials (bottom-left) → Settings → Privacy → **Export data**. You'll get an email with a ZIP. Download it within 24 hours — the link expires. Unzip it to `C:\Users\DanGi\Downloads\claude-export\`
- [ ] **Copy your Project instructions manually.** Projects and memory are NOT in that export. Open each Claude Project, copy its custom instructions into a text file, save as `claude-export/project-instructions.txt`
- [ ] **Put the guide in your repo.** Copy `PROJECT_JARVIS_Complete_Build.html` into `SummitOS/docs/`
- [ ] **Gather your source material** into one folder, `C:\Users\DanGi\Downloads\jarvis-ingest\`:
  - Summit Voice AI Sales Playbook PDF
  - Any training manuals, SOPs, scripts
  - Your best-performing outreach emails (for voice/style learning)
  - ICP notes, offer docs, pricing sheets
  - The 18 repo/skill screenshots
- [ ] **Know your paths.** Run `echo $env:USERPROFILE` in PowerShell. Confirm your SummitOS repo path.
- [ ] **Commit your current work.** `git add -A && git commit -m "pre-jarvis checkpoint"` — so you can always roll back.

---

## PROMPT 0 — Audit & Architecture Plan
*Run this first. Do not let it write code yet. This is the most valuable prompt in the file.*

```
You are architecting a major addition to Summit OS, my existing business operating
system. Before writing any code, I want a full audit and a plan.

CONTEXT TO READ FIRST:
1. Read docs/PROJECT_JARVIS_Complete_Build.html. This is a build guide I had
   written for a standalone Windows Jarvis assistant. Treat it as a SPECIFICATION
   of desired capabilities, not as code to import. It is human documentation.
2. Read the entire Summit OS codebase. Map the actual architecture: frontend
   framework and structure, backend endpoints, database schema, auth flow,
   deployment setup, scheduled jobs, and every external integration.

WHO I AM:
Dan Gill, solo founder of Summit Voice AI. I sell an AI voice + automation system
("Ava") to roofing contractors in the US. 9 active clients, goal is $100K+ MRR as
a one-person company. ~10 years roofing industry experience. I close sales calls;
everything else must run without me. I am not a strong developer — explain your
work in plain English.

WHAT I WANT BUILT (the end state):
A "Jarvis" layer inside Summit OS. A tab in the UI where I sign in and talk to an
AI that has total context on my business, my writing voice, my clients, and my
systems. It can see and act on the operating system, my calendar, my email, and
my GoHighLevel CRM. I can also text it and call it a real phone number. Its
long-term memory lives in a local Obsidian vault of markdown files.

DELIVER THIS AUDIT, IN PLAIN ENGLISH, AS A MARKDOWN FILE AT docs/JARVIS_PLAN.md:

PART 1 — Current state audit
- Architecture map of Summit OS as it actually exists today
- What is built well and should be left alone
- What is fragile, duplicated, or will break under load
- Security review: exposed secrets, missing auth, unsafe endpoints, RLS gaps
- Dead code, unused dependencies, and abandoned features
- Anything that will actively fight against adding a Jarvis layer

PART 2 — Integration plan
- Exactly where the Jarvis service should live in my existing architecture and why
- Whether it should be a new service, a module in the current backend, or both
- The data flow for: UI chat, voice, SMS, phone call, and scheduled autonomous runs
- What existing code can be reused versus what must be written new
- Database schema changes required
- A risk list: what could break in production, and how we avoid it

PART 3 — Build sequence
- An ordered list of work packages, each independently testable and shippable
- For each: what it does, what it depends on, rough effort, and how I verify it
- Explicitly flag anything that requires a decision or credential FROM ME

PART 4 — Honest pushback
- Tell me where my plan is wrong, overcomplicated, or a bad idea
- Tell me what I am underestimating
- Tell me what to cut from v1 to ship faster
- If any capability I described is not actually achievable as I imagine it,
  say so directly and propose the closest real alternative

RULES:
- Write NO implementation code in this response. Plan only.
- Do not flatter the existing code. I need the real state, not encouragement.
- If something is genuinely good, say so briefly and move on.
- End with a numbered list of everything you need from me before Prompt 1.
```

---

## PROMPT 1 — The Obsidian Memory Vault & Total Context Ingestion
*This is what makes Jarvis know everything. Run after you've reviewed the plan.*

```
Build the memory foundation for Jarvis. This is the layer that gives it total
context on me and my business.

STEP 1 — Create the vault
Create an Obsidian vault at C:\Users\DanGi\SummitVault (or confirm the path with
me if that conflicts with something). Structure:

  /00-Jarvis/          identity.md, rules.md, capabilities.md
  /01-Business/        offer.md, icp.md, pricing.md, revenue-math.md,
                       competitors.md, objection-handling.md
  /02-Voice/           writing-style.md, email-templates.md, call-scripts.md
  /03-Clients/         one file per active client
  /04-Systems/         architecture.md, runbooks.md, credentials-map.md
                       (names and locations of secrets, NEVER the secret values)
  /05-Knowledge/       ingested reference material
  /06-Conversations/   processed Claude history
  /07-Memory/          rolling facts Jarvis learns, one file per month
  /08-Daily/           daily notes and briefings
  /09-Projects/        active builds and their status
  /10-Logs/            audit trail of every action Jarvis takes

STEP 2 — Ingest my Claude conversation history
I have exported my full Claude history to C:\Users\DanGi\Downloads\claude-export\
It contains conversations.json plus a project-instructions.txt I made manually.

Write a Python script scripts/ingest_claude_history.py that:
- Parses conversations.json
- Converts each conversation to a clean markdown file with YAML frontmatter
  containing: title, date, model, topic tags, and a one-line summary
- Auto-categorizes by topic (sales, code, content, strategy, personal, other)
- SKIPS anything containing an API key, password, or token pattern, and logs
  what it skipped so I can review
- Writes output to /06-Conversations/ organized by year-month
- Generates /06-Conversations/INDEX.md — a searchable index of every conversation
- Generates /06-Conversations/DISTILLED.md — the important part: a synthesized
  document of every durable decision, preference, and lesson across all my
  history, deduplicated, so Jarvis reads one file instead of thousands

STEP 3 — Ingest my business material
Everything in C:\Users\DanGi\Downloads\jarvis-ingest\ (PDFs, docs, images).
Extract text, convert to markdown, file into the right vault folder.
The Sales Playbook PDF is authoritative for voice and revenue math.

STEP 4 — Learn my writing voice
From my outreach emails, playbook, and conversation history, generate
/02-Voice/writing-style.md that captures how I actually write. Include real
example snippets. My known rules: Hormozi-influenced, short sentences separated
by line breaks, direct, no fluff, never salesy, no em dashes (use ellipses),
lowercase email subject lines, sentence case elsewhere, never name the product
on first touch in cold outreach. Add whatever else you detect from the corpus.

STEP 5 — Build the memory engine
- A retrieval layer over the vault so Jarvis loads relevant context per query
  rather than dumping the whole vault into every prompt. Use embeddings with a
  local vector store, or an equivalent approach you recommend and justify.
- A write path: when Jarvis learns a durable fact, it appends to
  /07-Memory/YYYY-MM.md with a timestamp and source.
- Always-loaded core: 00-Jarvis/identity.md, 00-Jarvis/rules.md, and a compact
  business summary. Everything else retrieved on demand.
- Never delete vault files. Append or create only.

STEP 6 — Report
Tell me: how many conversations were ingested, what got skipped and why, what
you learned about my writing voice, and what gaps you found in my business
documentation that I should fill in.

Show me your plan for each step before executing it.
```

---

## PROMPT 2 — The Jarvis Service (brain, tools, memory wiring)

```
Build the Jarvis backend service inside Summit OS, following docs/JARVIS_PLAN.md.

CORE:
- A service exposing: POST /jarvis/chat (text), POST /jarvis/voice (audio),
  WS /jarvis/stream (live state + streaming tokens), GET /jarvis/health
- Loads identity.md and rules.md from the vault on every request
- Retrieves relevant vault context per query via the memory engine from Prompt 1
- Model routing: capable model for reasoning and writing, fast/cheap model for
  structured extraction and classification. One config file controls this.
- Streams responses token by token
- Logs every tool call to /10-Logs/YYYY-MM-DD.md

TOOLS — SYSTEM AWARENESS (read-only, run freely):
- summit_status: pulls from my existing endpoints (/clients, /agents/status,
  /analytics/activity-feed) and returns a plain-English business state
- read_files: search and read anything on my machine
- running_processes: what dev servers, builds and scheduled tasks are active
- project_status: git branch, uncommitted changes, last commit, for any repo
- calendar_today / calendar_week: read my calendar
- email_triage: read recent email, classify by urgency, summarize what needs me
- ghl_needs_response: query GoHighLevel for conversations awaiting a reply,
  ranked by lead score and time waiting. This is a daily driver for me.

TOOLS — ACTIONS (see the confirmation policy below):
- draft_reply: writes a response in MY voice using /02-Voice/, returns for review
- send_reply: sends an email or GHL message I have explicitly approved
- schedule_event: creates a calendar event
- create_note: writes to the vault
- start_build: scaffolds a project and launches a Claude Code session
- generate_document: proposals, one-pagers, PDFs, decks using my design standard
  (dark navy #0B1120, teal #0FA8C8 accent, Georgia display), saved to /09-Projects/
- scrape_leads: Apollo, by city
- build_demo_site: triggers my demo machine
- dispatch_outreach: my existing /dispatch endpoint

CONFIRMATION POLICY — implement exactly this, no shortcuts:
- Read-only tools: run immediately, no confirmation.
- Single explicit action I directly commanded in this conversation
  ("draft a reply to Mike and send it"): execute it, then report what was done.
- Bulk actions (more than 3 recipients), anything unattended or scheduled,
  anything that spends money at scale, any deploy, any delete, any force push:
  ALWAYS show a full preview and require explicit approval first.
- Build a single shared gate function so this cannot be bypassed per-tool.
- Every action, gated or not, is logged to /10-Logs/.

SECURITY:
- All secrets from environment variables. Never in frontend code, never in the vault.
- The vault stores the NAMES and LOCATIONS of credentials, never the values.
- Verify .gitignore covers .env before you commit anything.

Build the read-only tools first and let me test them before you build any
action tools.
```

---

## PROMPT 3 — The Jarvis Tab in the Summit OS UI

```
Build the Jarvis interface inside the Summit OS frontend. Match my existing
app's stack, routing, auth, and component conventions exactly — read the codebase
and follow what is already there rather than introducing new patterns.

ROUTE: a new authenticated "Jarvis" tab in the main navigation.

LAYOUT — three zones:

1. THE ORB (top center, roughly 260px)
   - Three.js particle sphere, about 2000 particles, GLSL shader driven
   - State colors: idle cyan #3BE8FF slow rotation | listening green #41F5A0
     particles pull inward | thinking amber #FFB020 fast turbulent motion |
     speaking bright cyan with radius pulsing to audio amplitude |
     error red #FF6B6B
   - Reads live state from the WS /jarvis/stream connection
   - Must degrade gracefully: if WebGL is unavailable, show a CSS fallback

2. CONVERSATION (center)
   - Streaming markdown responses
   - Push-to-talk mic button plus a text input
   - Tool calls render as compact inline cards showing what it did
   - Confirmation prompts render as clear Approve / Reject cards with the full
     preview visible before I can approve
   - Conversation history persisted and searchable

3. LIVE SYSTEM PANEL (right sidebar, collapsible)
   - Active clients, agent health, last 24h outreach activity
   - Running builds and dev servers
   - Today's calendar
   - Count of GHL conversations awaiting response, clickable to act on
   - Auto-refreshing, with a visible last-updated timestamp

DESIGN: dark HUD aesthetic consistent with Summit OS. Dark navy base, teal/cyan
accent, thin precise lines, monospace for data and labels. Restrained motion —
the orb is the one bold element, everything else stays quiet and disciplined.
Fully responsive, keyboard accessible, respects prefers-reduced-motion.

Do not break or restyle any existing Summit OS page. This is additive only.
```

---

## PROMPT 4 — Voice, Text, and Phone Channels

```
Add the three external channels to Jarvis, following Part 7 of
docs/PROJECT_JARVIS_Complete_Build.html. Each routes into the SAME brain, tools,
memory, and confirmation gates as the UI. No duplicated logic.

CHANNEL 1 — Voice in the browser
- Speech to text via Groq Whisper (whisper-large-v3-turbo)
- Text to speech via ElevenLabs, voice ID from env
- Stream TTS sentence by sentence so it starts speaking before the full answer
- Emit audio amplitude over the WebSocket so the orb pulses with the voice

CHANNEL 2 — Telegram
- Long polling so no public URL is needed
- Hard lock to my TELEGRAM_CHAT_ID; reject and log everything else
- Proactive notifications: build finished, agent failed, a lead scored above 80,
  a confirmation is waiting on me

CHANNEL 3 — Phone (Twilio)
- Deploy as a separate always-on service so it works while my PC is asleep
- Twilio ConversationRelay: POST /twiml returns TwiML opening a Connect Stream,
  /ws handles the conversation
- THREE security layers, all required: verify the Twilio request signature on
  every request, require a spoken PIN before any tool runs, and allow-list my
  own caller IDs
- On the phone channel, confirmations are spoken and must be verbally confirmed

Give me the exact deployment steps and the exact URL to paste into the Twilio
console when you are done.
```

---

## PROMPT 5 — The One-Man-Army Agents

```
Now build the autonomous layer that lets me operate like a team. Each of these
runs on a schedule, writes results to the vault, and notifies me via Telegram
when it needs a decision. Nothing sends externally without my approval.

AGENT 1 — Morning Briefing (daily 6am)
Calendar, urgent email, GHL conversations awaiting response ranked by priority,
client and agent health, running builds, yesterday's unfinished items. Delivers
a spoken summary under 45 seconds plus a written note to /08-Daily/.

AGENT 2 — Inbox & CRM Triage (every 2 hours, business hours)
Scans email and GHL. Classifies by urgency and revenue impact. DRAFTS responses
in my voice for everything needing a reply and queues them for one-click approval.
Never sends on its own.

AGENT 3 — Pipeline Watch (daily)
Scores and ranks open opportunities. Flags deals going cold, deals with no next
step, and leads scoring above 80 that have not been contacted. Tells me the
three highest-leverage actions for the day and why.

AGENT 4 — Content Engine (weekly)
Researches what is actually happening in roofing and voice AI. Generates a week
of content in my voice — social posts, email angles, one long-form piece. Saves
to the vault for review. Nothing publishes without approval.

AGENT 5 — Prospect Researcher (on demand + daily batch)
Given a city or a company, researches the business, finds the owner, estimates
their missed-call revenue loss using my $9,500 average job value math, and
produces a personalized angle for outreach.

AGENT 6 — Build Watchdog (continuous)
Monitors deployments, error rates, and agent health across Railway, Vercel and
Supabase. Alerts on failures with a diagnosis and a proposed fix.

AGENT 7 — Weekly Business Review (Friday)
MRR movement, client health and churn risk, what worked and what did not,
where my time actually went, and a recommendation for next week's single
highest-leverage focus. Honest assessment, not a cheerleading report.

For each agent: build it, show me the output on a real run, and let me tune it
before you schedule it. Log every run to /10-Logs/.

Then, based on everything you now know about my business from the vault, tell me:
what OTHER agent would move me toward $100K MRR fastest that I have not thought
to ask for? Make the case for it, then build it if I agree.
```

---

## PROMPT 6 — Hardening, Audit & Honest Assessment
*Run this last. Then re-run it monthly.*

```
Full review of everything we built. Be rigorous and do not flatter the work.

SECURITY AUDIT
- Every secret: where is it, is it exposed anywhere, is .gitignore correct
- Every endpoint: is it authenticated, is it rate limited, can it be abused
- The phone channel specifically: signature verification, PIN, caller allow-list
- The Telegram channel: chat ID lock actually enforced
- Confirmation gates: try to bypass them. Report anything that got through.
- Supabase RLS coverage on any new tables

RELIABILITY AUDIT
- What happens when each external API is down or rate limited
- What happens on a malformed or hostile input
- Where can this loop infinitely or run up a bill
- Cost projection per month at my usage, with the biggest cost drivers named

QUALITY AUDIT
- Does Jarvis actually sound like me, tested against real examples from my vault
- Is memory retrieval returning relevant context, or noise
- Where does it hallucinate business facts instead of reading the vault
- Test the confirmation gates with adversarial phrasing

THEN, THE PART I ACTUALLY WANT:
Write docs/JARVIS_ASSESSMENT.md containing:
1. What we built that is genuinely good
2. What is fragile and will break, ranked by likelihood
3. What I asked for that we built but I probably will not use, and should cut
4. What is missing that would matter most for a one-person $100K MRR agency
5. Where I am fooling myself about what this system can do
6. The single highest-leverage improvement to make next, and why

Be direct. I would rather hear the problem now than discover it with a client
on the phone.
```

---

## AFTER EACH PROMPT — verify before continuing

| After | Test |
|---|---|
| Prompt 0 | Read `docs/JARVIS_PLAN.md` end to end. Push back on anything that feels wrong. |
| Prompt 1 | Ask Jarvis: *"What do you know about how I write, and what were the last three big decisions I made?"* |
| Prompt 2 | `curl` the health endpoint, then ask for a business status via /jarvis/chat |
| Prompt 3 | Sign into Summit OS, open the Jarvis tab, watch the orb change state as it responds |
| Prompt 4 | Text the Telegram bot. Then call the Twilio number from your cell. |
| Prompt 5 | Let each agent run once manually and read its output before scheduling it. |
| Prompt 6 | Read the assessment. Act on item 6. |

---

## THINGS TO WATCH FOR

**If Claude Code says a capability isn't feasible** — believe it and ask for the closest real alternative. That's more useful than forcing an approach that half-works.

**If the vault ingestion produces noise** — it's better to have 200 well-distilled facts than 8,000 raw conversation dumps. The `DISTILLED.md` file matters more than the raw archive.

**If a confirmation gate ever fires when it shouldn't, or fails to fire when it should** — stop everything else and fix it. That gate is the difference between leverage and a very bad afternoon.

**Cost control** — set an auto-reload cap in the Anthropic console you're genuinely comfortable with. Agents running on schedules can surprise you in month one. Review spend weekly until the pattern is stable.
