# Jarvis / SummitOS — Status & Next Steps

Living document. Update this after finishing any Jarvis/SummitOS work so a new
session (or future you) can pick up without re-discovering everything from
scratch. Last updated: 2026-08-15.

## The vision (why any of this matters)

Jarvis should function like a real executive team, not a chatbot: proactively
manage the calendar, screen and triage inbound leads, keep Dan briefed without
being asked, place and take calls, draft and send emails, enrich prospect
data, and generally run day-to-day operations — reachable from Slack, phone,
or text, from anywhere. Every fix below is in service of that, not novelty.

## What's real right now (verified working in production)

- **Backend**: FastAPI app (`ava_demo_studio_api.py` + `jarvis_integrations.py`)
  deployed on Railway (`ava-studio-api` project), deployed via `railway up`
  (direct upload — **not** git-triggered; a `git push` alone does NOT deploy
  the backend, you must also run `railway up --service ava-studio-api`).
- **Frontend dashboard**: `summit-os-dashboard` on Vercel, now its own
  dedicated repo (`Dgill757/Summit-OS-ava-studio`) as of 2026-08-14's
  migration — no longer shares a repo with the marketing site.
- **Integrations confirmed `ready: true` in production** (checked live via
  `GET /jarvis/integrations/status`): GHL, Google Calendar, Gmail, Google
  Drive, Slack (conversation + notifications), Twilio (SMS + voice),
  Telegram, web research (Firecrawl).
- **Reachable from a Slack conversation right now**: calendar (view
  availability, create events), Gmail (search, inbox triage, draft, send),
  meeting prep (pulls calendar + Gmail + GHL + company research into one
  dossier), Slack messaging, SMS, **outbound phone calls** ("call me" /
  "call my phone"), local computer read tools (files/git/processes).
- **Outbound phone calling**: `/jarvis/phone/call` — real Twilio call, PIN
  authenticated, connects to a live conversational voice loop
  (`/jarvis/phone/twiml` + websocket brain). This already existed; it just
  wasn't reachable from chat until 2026-08-15.
- **Proactive notification system** (new 2026-08-15): `POST /jarvis/notify`
  on the Railway backend — Slack always fires, a phone call only fires when
  `urgent: true`. This is the single relay point for any local script that
  needs to reach Dan, and it works because it uses Railway's real Slack
  credentials instead of each script's own (broken) local webhook.
  - `c:\Users\DanGi\scripts\jarvis_notify.py` — shared Python helper other
    local scripts should import (`from jarvis_notify import notify`) instead
    of posting to `SLACK_WEBHOOK_URL` directly.
- **The daily business scraper actually runs now**: `Summit Google Business
  Scraper` scheduled task, 6am daily, runs
  `C:\Users\DanGi\outreach\daily_outreach.py`. Apify (Google Maps) is
  primary — free, returns company/phone/website/email in one call. Apollo is
  bounded enrichment only: free search to check if a decision-maker has an
  email on file, paid reveal call only fires for leads scoring 80+
  (`score_lead()`). Live-tested 2026-08-14: 12 real GHL contacts created
  before hitting an (since-fixed) Unicode crash.
- **Hot-lead reply monitoring, screened** (rebuilt 2026-08-15):
  `C:\Users\DanGi\scripts\ghl_reply_monitor_fixed.py`, runs every 15 min via
  "Summit Reply Monitor Fixed". Classifies every inbound GHL reply as
  `stop` / `auto` / `human` before ever alerting:
  - `stop` → tags contact "Opted Out" + "Do Not Contact" in GHL, no Slack
    ping (compliance-correct, never re-contact these).
  - `auto` → known bot/auto-responder signatures (Podium's "thanks for
    texting, we'll be with you shortly" canned reply, out-of-office, etc.) →
    suppressed.
  - `human` → real reply → Slack-pings Dan via `/jarvis/notify`.
  - State is persisted per-conversation in `reply_monitor_state.json` so the
    same message is never re-alerted, no matter how many times GHL still
    reports it "unread." (Previously this did NOT exist — the old version
    re-alerted the same 5 stale conversations every 15 min forever;
    `hot_leads.log` had ~20,000 duplicate lines before the fix.)

## What was actually broken (root causes, for context)

Found during the 2026-08-14/15 sessions — the system had a lot of real
capability that was invisibly disconnected:

1. **Daily Jarvis agent ran blind for days.** `run_daily_agent.bat`'s `cd`
   target folder had been renamed/moved; `cd` failing in a `.bat` doesn't
   abort, it silently falls through to `C:\Windows\System32`, losing all
   file/MCP access. Fixed.
2. **`ghl` MCP server never worked, ever, in any session** — it lived in
   `~/.claude/mcp.json`, a file Claude Code doesn't read, using the wrong
   transport type. Properly registered via `claude mcp add` at user scope
   now (Streamable HTTP, not SSE — that GHL endpoint doesn't speak legacy
   SSE transport).
3. **The scraper had literally no scheduled task.** Not disabled — never
   existed. `state.json` had been stuck on June 6 for two months. Nothing on
   the machine ever called `outreach\daily_outreach.py`.
4. **Apollo's search API was deprecated** (`mixed_people/search` → 422).
   Migrated to `mixed_people/api_search`, and discovered along the way that
   Apollo now charges a separate credit for contact reveal — redesigned
   around that instead of blindly porting the old call.
5. **Two redundant reply-monitor scripts**, one silently broken (likely the
   same deprecated-param issue pattern), one working but with zero dedup —
   the working one is what caused the Slack spam. The broken redundant one
   (`SummitVoiceAI-ReplyMonitor` task) is now disabled.
6. **9 local scripts' Slack delivery was silently dead** — `SLACK_WEBHOOK_URL`
   in `c:\Users\DanGi\scripts\.env` is still the literal placeholder
   `YOUR_WEBHOOK_HERE` and always has been. Every agent that only knew how to
   post there has never actually reached Dan. `jarvis_notify.py` (see above)
   fixes this with one shared fallback; wired into 4 scripts so far (morning
   briefing, weekly CEO report, client churn alerts, hot-lead replies).

## Next steps (roughly priority order)

- [ ] **Wire the remaining 6 scripts to `jarvis_notify`** — same broken
      placeholder-webhook pattern, same fix (`from jarvis_notify import
      notify`, replace the direct-webhook block): `daily_growth_coach.py`,
      `research_agent.py`, `content_generator.py`, `ghl_daily_outreach.py`,
      `heygen_agent.py`, `social_media_automation.py`.
- [ ] **Or better: get a real Slack webhook URL from Dan** and fill in
      `c:\Users\DanGi\scripts\.env` and `c:\Users\DanGi\outreach\.env` —
      `jarvis_notify.py` already prefers a real webhook over the Railway
      fallback when one exists, so this is a zero-code fix, just needs the
      URL created in Slack (Apps → Incoming Webhooks) and pasted in.
- [ ] **Vercel repoint still pending** from the 2026-08-14 migration — Dan
      needs to manually disconnect `summit-os-dashboard` from
      `Dgill757/SMGWebsite` and connect it to `Dgill757/Summit-OS-ava-studio`
      in the Vercel dashboard (Settings → Git). Not done via API/CLI on
      purpose — see the migration report for why.
- [ ] **Old shared repo cleanup** — once the Vercel repoint above is
      confirmed working, delete the `summit-os` branch from
      `Dgill757/SMGWebsite` so that repo has zero SummitOS content left
      (`git push https://github.com/Dgill757/SMGWebsite.git --delete
      summit-os`).
- [ ] **Scheduled (not just event-driven) proactive check-ins.** Dan wants
      "both" trigger types. Event-driven (hot lead replies) is live. Scheduled
      check-ins beyond the 7am briefing (e.g. midday pipeline check, evening
      wrap-up) aren't built yet — would reuse `daily_executive_inputs()`
      (already aggregates calendar + inbox triage + no-website prospects +
      pipeline health) plus a "is this actually worth surfacing" judgment
      layer before pinging Slack, so it doesn't become the same kind of noise
      problem the reply monitor had.
- [ ] **Other daily agents' actual output quality is unverified.** Business
      Intel, GHL Pipeline Manager, System Watchdog, and the rest all run
      successfully (`LastTaskResult: 0`) but "ran without crashing" was
      already proven false as a signal of "did something useful" — the daily
      briefing agent ran "successfully" for days while doing nothing. Worth
      spot-checking a few of these the same way the scraper and reply monitor
      were checked, not just trusting the green checkmark.
- [ ] **`search_apollo_roofing_leads()`** (the old Apollo-primary bulk search
      function in `daily_outreach.py`) is now unused — left defined but not
      called, in case a higher Apollo plan later makes bulk-reveal
      economical again. Not deleted on purpose.
- [ ] **Website building, content creation, data enrichment "on demand"** —
      the user's stated end-goal includes Jarvis building websites and
      creating content on request. `premium_website_generator.py`,
      `content_generator.py`, `no_website_builder.py` etc. already exist as
      standalone scripts but aren't wired as callable tools from the
      conversational Jarvis brain the way calendar/Gmail/calls now are —
      worth doing the same `WRITE_TOOLS` wiring pass on these if Dan wants
      "build me a demo site for X" to work from Slack/phone directly instead
      of him running a script manually.

## Operating notes / gotchas for future sessions

- **Railway deploy is manual and separate from git.** `git push` alone does
  NOT update the live backend. After any `ava_demo_studio_api.py` or
  `jarvis_integrations.py` change: commit + push (for history), then
  `railway up --service ava-studio-api --detach` from the SummitOS repo root
  (already linked). The new deploy runs alongside the old one during
  rollout — a request can 404 for a minute or two before the new version is
  actually serving; poll the endpoint you just added rather than trusting
  `/health` (a generic route that exists on every version).
- **CLAUDE.md's "never modify existing scripts without permission" rule** —
  Dan has now given broad standing permission for infrastructure/reliability
  fixes across this session ("do whatever the most optimized fix would be").
  Still worth a quick explicit check before anything that changes outreach
  message content, deletes data, or spends money in a new way (e.g. the
  Apollo credit-reveal gating was a cost decision, not just a bug fix, and
  was confirmed with Dan first).
- **Two Python installs exist** (`C:\Python314` and
  `AppData\Local\Programs\Python\Python313`) — scheduled tasks reference both
  inconsistently. Not currently causing problems (each task pins its own
  interpreter) but worth knowing if a "works when I run it, fails in Task
  Scheduler" issue ever comes up.
- **`outreach_tracker.db`** is a legacy tracking DB tied to the old
  Apollo/Apify-into-SMS-sequence campaign (`ghl_daily_outreach.py` /
  `ghl_reply_monitor.py`). The new daily scraper (`daily_outreach.py`)
  creates GHL contacts directly and does NOT write to this DB — they're
  separate systems. Don't assume contact counts from one reflect the other.
