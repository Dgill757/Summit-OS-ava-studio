# PROMPT 01 — EXECUTE
### Paste into Claude Code after it delivers SUMMIT_OS_MASTER_PLAN.md

```
Good work on the plan. I've read your findings and I agree with your pushback.
Here's what we're doing. Work through it in order. Don't skip ahead, and don't
batch multiple packages into one commit.

═══════════════════════════════════════════════════════════════
WHY THIS MATTERS — read this before you start
═══════════════════════════════════════════════════════════════

I'm one person running Summit Voice AI. Nine clients. Goal is $100K+ MRR. There
is no team and there's no one to hire. My only job is closing sales calls. Every
hour I spend on operations is an hour not spent selling, and selling is the only
thing that grows this.

So the standard I'm holding you to: when you tell me something is done, I need to
be able to trust it's actually done and actually live. Your own audit found that
I believed a security fix was deployed when the deploy config was pointing at the
old file the whole time. That's the failure mode that kills me — not bugs, but
believing something works when it doesn't. I make decisions on top of what you
tell me.

Build less if you have to. Make it solid.

═══════════════════════════════════════════════════════════════
PACKAGE 0 — FIX THE EXPOSURES
═══════════════════════════════════════════════════════════════

Do these in this order, most damaging first.

0.1  Resolve the two-dashboard problem.
     vercel.json deploys the old index.html with the database key and the
     password ava2026 readable in plain JavaScript via View Source. The secure
     version in vercel_deploy/ routes through the server correctly.
     Make the secure one the only one that exists. Delete or archive the
     insecure file so it can never be accidentally deployed again. Update
     vercel.json. Then verify against the LIVE deployed site, not the local
     file, that no key or password appears in the served source.

0.2  Add authentication and rate limiting to /dispatch.
     It's currently open — anyone with the Railway URL can trigger demo builds
     and burn my Anthropic and Firecrawl credits. Add auth consistent with how
     the rest of my API handles it, plus a sane rate limit.
     Then audit EVERY other endpoint on that backend for the same problem and
     fix any others you find.

0.3  Rotate the exposed credentials.
     The Supabase key in the public repo is revoked but should be rotated and
     removed from the codebase properly. The GHL private token was in public
     HTML for weeks and is in plain text in my global CLAUDE.md.
     Tell me exactly which dashboard, which menu, and which button for each
     rotation, and what I need to update afterward once I have the new values.
     Note: going private does not fix an exposed key. Git history retains it and
     anyone who already cloned it still has it. Rotation is the only real fix.
     Treat "made the repo private" as insufficient.

0.4  Sweep for anything else.
     Scan the entire codebase and all config for hardcoded secrets, keys,
     tokens, passwords, and connection strings. Check git history too. Give me
     a complete list of what you found and where.

0.5  Then check my Anthropic usage.
     I recently got a "credit balance too low" HTTP 400. I also had an
     unauthenticated /dispatch burning credits. Pull whatever usage data you can
     access and tell me whether the spend pattern around that error looks like
     normal usage or looks like abuse. If you can't determine it from available
     data, tell me exactly where in the Anthropic console to look myself.

═══════════════════════════════════════════════════════════════
PACKAGE 0.5 — THE CLASS OF BUG, NOT THE INSTANCE
═══════════════════════════════════════════════════════════════

The vercel.json finding means a security fix I believed was live never was. That
scares me more than the specific bug, because it means my mental model of what's
running is wrong.

Audit every deployment configuration against what is actually running in
production. Vercel, Railway, GitHub Actions, Supabase, Windows Task Scheduler —
all of it.

For each one tell me: what I probably think is deployed, what's actually
deployed, and whether they match. Write this to docs/DEPLOYMENT_TRUTH.md as a
reference I can re-check later.

Flag anything else I likely believe is working that isn't.

═══════════════════════════════════════════════════════════════
PACKAGE 1 — GET MY BUSINESS OFF MY LAPTOP
═══════════════════════════════════════════════════════════════

You buried this in the pushback section but I think it's the most important
finding in your whole audit, so I'm promoting it ahead of all Jarvis work.

I have 11 automated scripts running on Windows Task Scheduler on this machine.
If I close my laptop for three days, my scraping, follow-up, and reactivation
silently stop while I believe they're running. That's a direct contradiction of
the one requirement this whole system exists to satisfy.

Migrate everything that must run on a schedule off my laptop and onto
always-on infrastructure — Railway cron or equivalent. For each of the 11 scripts
tell me: what it does, whether it actually needs to run on a schedule, whether it
can move, and what it depends on locally that would block the move.

Then build a heartbeat: something that tells me when a scheduled job fails or
doesn't run, instead of failing silently. Silent failure is the enemy here.

If some genuinely can't move, tell me which and why, and what the fallback is.

═══════════════════════════════════════════════════════════════
PACKAGE 2 — THE REBRAND
═══════════════════════════════════════════════════════════════

You found my dashboard already uses CSS variables in one :root block, so this
should be fast.

Apply the palette from PROMPT_00 across all of Summit OS. Cyan #3BE8FF primary,
amber #FFB020 secondary, green #41F5A0 success, red #FF6B6B error, on the deep
navy backgrounds. Chakra Petch for display, Inter for body, JetBrains Mono for
data and labels.

Rules:
  - Every color as a token in one place. No hardcoded hex in any component.
  - Find and replace the stragglers you identified.
  - Keep the old palette defined but unused so I can revert instantly.
  - Its own commit, separate from everything else.
  - Check contrast ratios. Clients see these screens.
  - Break nothing. If styling and logic are tangled in a component, tell me
    before refactoring it.

Then show me one screen and let me confirm I like it before you do the rest.

═══════════════════════════════════════════════════════════════
PACKAGE 3 — THE ONE THING (build this, skip the rest for now)
═══════════════════════════════════════════════════════════════

I'm taking your recommendation. Build the Morning Briefing plus the "who needs a
reply" queue with drafts in my voice. Reuse morning_ceo_briefing.py.

  - Runs on a schedule on always-on infrastructure, not my laptop
  - Surfaces GHL conversations awaiting a response, ranked by lead score and how
    long they've been waiting
  - Drafts a reply for each one in my writing voice
  - Delivered in the dashboard and via Telegram
  - One-click approve to send. Nothing sends unattended or in bulk without me.
  - Also surfaces: today's calendar, urgent email, client and agent health

My writing voice: Hormozi-influenced, short sentences separated by line breaks,
direct, no fluff, never salesy, no em dashes (use ellipses), lowercase email
subject lines, sentence case elsewhere. Anchor to the revenue math — $9,500
average job, 1,095 to 1,825 missed calls a year, $1.56M to $8.67M recoverable.
Calendly link only on positive replies, never a first touch.

Speed of reply is the number one lever on closing roofing leads. This is the
piece that makes me money. Everything else in the Jarvis vision can wait.

═══════════════════════════════════════════════════════════════
DEFERRED — do not build these yet
═══════════════════════════════════════════════════════════════

Cut from v1, per your recommendation and my agreement:
  - The phone channel. Worst risk-to-value trade in the plan. Revisit month two.
  - Voice input and output. Text first.
  - The desktop orb overlay.
  - The remaining 6 agents.
  - Vector memory and full Claude history ingestion.

We'll build the Obsidian vault and the rest of the agents after Package 3 is
live and I've used it for a week. Don't start them early.

═══════════════════════════════════════════════════════════════
HOW TO WORK
═══════════════════════════════════════════════════════════════

  - Small, reviewable, revertible commits. One package per commit minimum.
  - After each package, give me one command or one URL to verify it myself.
  - Verify against what's actually deployed, never against the local file.
  - Explain in plain English. I'm a founder, not an engineer.
  - If you need a credential or a decision from me, stop and ask. Don't stub it
    and keep going.
  - If something I've asked for is wrong or won't work, say so before building it.
  - When you finish a package, tell me plainly what is now true that wasn't
    before, and what I should test.

═══════════════════════════════════════════════════════════════
THE OUTCOME I'M PAYING FOR
═══════════════════════════════════════════════════════════════

Every morning I open Summit OS. In sixty seconds I know what my business did
overnight, who needs me, and what the highest-leverage thing I can do today is.
The replies are already drafted in my voice and I approve them with one click.
The scrapers and follow-ups ran whether or not my laptop was open. Nothing
failed silently.

Then I spend the rest of the day on sales calls while the system handles the
rest.

That's the whole goal. Start with Package 0.
```

---

## Order of operations on your end

1. Paste the prompt.
2. When it asks for the two live URLs, have them ready.
3. When it gives you rotation steps, do them immediately — don't batch them for later.
4. After Package 0.5, read `docs/DEPLOYMENT_TRUTH.md` carefully. That's the document that tells you whether your mental model of your own system is accurate.
5. Approve the rebrand on one screen before it does all of them.
6. Use Package 3 for a full week before building anything else.
