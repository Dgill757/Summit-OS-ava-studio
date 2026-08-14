# PROMPT 00 — THE MASTER BRIEF
### Paste this into Claude Code FIRST, before any other prompt.

> **Note:** This replaces nothing in your other prompt file — it goes *in front of* Prompt 0. This is the "here is the whole vision and the stakes" brief. After it responds with the plan and the list of what it needs from you, continue with Prompt 0 (audit) and onward.

---

```
Read this entire brief before responding. Do not write any code yet. I want you
to understand the whole picture first, then come back to me with a plan and a
list of everything you need from me.

═══════════════════════════════════════════════════════════════
WHO I AM AND WHY THIS MATTERS
═══════════════════════════════════════════════════════════════

I'm Dan Gill. I run Summit Voice AI. I sell an AI voice and automation system
to roofing contractors across the US. Nine active clients. My goal is $100K+ MRR.

I am one person. There is no team. There is no one to hire.

That's the actual constraint everything else follows from. Every hour I spend on
operations is an hour I'm not on a sales call, and sales calls are the only thing
that grows this business. I close deals. That's my job. Everything else has to
run without me or it doesn't get done.

Summit OS is the system I built to make that possible. It already runs a large
part of my business. What I'm asking you to build now is the layer that makes it
feel like a company instead of a solo operation.

I need this to work. Not "work as a demo" — work as the thing I open every
morning and trust with real client relationships and real revenue. If it's
half-built or unreliable, it costs me more time than it saves, and I'll abandon
it. So I would rather you build less and have it be solid than build everything
and have it be fragile.

═══════════════════════════════════════════════════════════════
THE VISION
═══════════════════════════════════════════════════════════════

Tony Stark doesn't have employees running his lab. He has JARVIS at the center
and an army of systems that execute. He talks, things happen. He asks a question,
he gets a real answer drawn from everything the system knows. The interface makes
him feel like he's operating something powerful, not filling in a form.

That's what I want Summit OS to become:

  - JARVIS at the center — one intelligence I talk to that has total context on
    my business, my writing voice, my clients, my systems, and my history
  - An army of AI agents around it — each one doing a job a human employee would
    otherwise do: triage, research, content, prospecting, monitoring, reporting
  - An interface that feels like a futuristic operating system, not a dashboard

Right now Summit OS is orange and black. It looks like a SaaS admin panel. I want
it to look and feel like the command center of a one-person company that punches
like a fifty-person company.

═══════════════════════════════════════════════════════════════
STEP 1 — READ THIS FIRST
═══════════════════════════════════════════════════════════════

There is a file at docs/PROJECT_JARVIS_Complete_Build.html.

Read it completely. It is a detailed build guide for a Jarvis assistant —
architecture, capabilities, voice, memory via an Obsidian vault, phone and text
channels, MCP tooling, agent design, and the exact visual language I want.

IMPORTANT: That file is a SPECIFICATION and a DESIGN REFERENCE. It is human
documentation. Do NOT import it into the app, do not render it in the UI, do not
treat its HTML as source code to reuse. Read it, understand the intent, and
extract two things:

  1. The capability spec — what Jarvis needs to be able to do
  2. The visual language — the exact aesthetic I want Summit OS to adopt

Then read my entire Summit OS codebase and understand what actually exists today.

═══════════════════════════════════════════════════════════════
STEP 2 — THE REBRAND
═══════════════════════════════════════════════════════════════

Replace the current orange-and-black branding across all of Summit OS with the
palette and design language from that HTML file. This is the exact token set:

  BACKGROUNDS
  --bg            #070B14   deep space navy, the base canvas
  --bg-2          #0A1020   slightly raised
  --panel         #0E1626   card and panel surfaces
  --panel-2       #111C30   elevated panels, modals

  STRUCTURE
  --line          #1B2942   default borders, dividers
  --line-bright   #26405F   emphasized borders, focused states

  ACCENTS
  --cyan          #3BE8FF   PRIMARY. Arc reactor blue. Actions, focus, active
  --cyan-dim      #1D9FB8   hover and pressed states
  --amber         #FFB020   SECONDARY. Warnings, pending, attention-needed
  --green         #41F5A0   success, healthy, connected
  --red           #FF6B6B   errors, failures, destructive actions

  TEXT
  --text          #E7EEFA   primary text
  --muted         #8DA0BF   secondary text, descriptions
  --muted-2       #5F718F   tertiary, timestamps, disabled

  TYPOGRAPHY
  Display / headings:  Chakra Petch (600-700 weight, slight letter-spacing)
  Body:                Inter
  Data, labels, code:  JetBrains Mono
  Small labels are uppercase, mono, letter-spaced ~0.2em, in cyan

  MOTION AND TEXTURE
  - Faint HUD grid overlay on the app background, very low opacity
  - Slow ambient scanline drifting down the page
  - Corner brackets on panels (small L-shaped cyan marks at opposing corners)
  - Scroll-reveal fade-and-rise on content sections
  - Restrained overall. One bold element per screen, everything else quiet.
  - Everything must respect prefers-reduced-motion

  THE PRINCIPLE
  Precision instrument, not video game. Thin lines, generous dark space, data
  rendered in monospace, color used for meaning rather than decoration. It should
  feel expensive and controlled. When something glows, it's because it matters.

HOW TO EXECUTE THE REBRAND — this part is important:

  - Define every color as a design token in ONE place (CSS custom properties,
    Tailwind config, or whatever my stack already uses). Never hardcode a hex
    value in a component.
  - Audit the codebase for every hardcoded color currently in use and replace
    each with the correct token. Give me a list of what you changed.
  - Keep the old palette defined but unused, so we can revert instantly if I
    hate it. Do not delete it until I confirm.
  - Do this as its own commit, separate from any functional changes, so the
    rebrand can be rolled back without losing the Jarvis work.
  - Every screen must remain fully readable and accessible. Check contrast
    ratios — dark themes fail accessibility easily and I have clients who will
    see these screens.
  - Do not break a single existing feature while restyling. If a component's
    logic and its styling are tangled together, tell me before you refactor it.

═══════════════════════════════════════════════════════════════
STEP 3 — WHAT GETS BUILT
═══════════════════════════════════════════════════════════════

Per the capability spec in that HTML file, the end state is:

  A JARVIS TAB in Summit OS where I sign in and talk to an AI that:
    - Has total context on my business through a local Obsidian vault
    - Knows my writing voice well enough to draft in it
    - Can see my calendar, email, files, running builds, and GoHighLevel CRM
    - Can tell me who needs a response and draft it for me
    - Can send it when I tell it to
    - Can schedule events, create documents, start builds, research prospects
    - Shows a live particle orb that reacts as it listens, thinks and speaks

  AN ARMY OF AGENTS running on schedules around it: morning briefing, inbox and
  CRM triage, pipeline watch, content engine, prospect researcher, build
  watchdog, weekly business review.

  THREE WAYS TO REACH IT: the UI, text message, and a real phone number I can
  call from anywhere.

  A MEMORY VAULT ingesting my entire Claude conversation history, my Sales
  Playbook, my training material, my ICP, my offers, and my writing samples.

You do not have to build all of this in one pass. I have a separate sequenced
prompt file for the implementation. What I need from you right now is the plan.

═══════════════════════════════════════════════════════════════
STEP 4 — AUDIT MY EXISTING SYSTEM
═══════════════════════════════════════════════════════════════

While you're in there, I want an honest audit of everything I've already built.
I'm not a strong developer. I have almost certainly done things wrong. I would
rather find out from you now than from a client later.

Tell me:
  - What's architected well and should be left alone
  - What's fragile, duplicated, or will break under load
  - Security problems: exposed secrets, missing auth, unsafe endpoints, RLS gaps
  - Dead code, unused dependencies, abandoned half-features
  - What will actively fight against adding a Jarvis layer
  - Where I'm paying for something I don't need, or could do cheaper
  - Anything that would embarrass me if a technical buyer looked at it

Do not soften this. Do not praise things to be encouraging. If something is bad,
say it's bad and tell me what to do instead. If something is genuinely good, one
sentence is enough.

═══════════════════════════════════════════════════════════════
WHAT I EXPECT FROM YOU IN THIS RESPONSE
═══════════════════════════════════════════════════════════════

No implementation code yet. Write a file at docs/SUMMIT_OS_MASTER_PLAN.md
containing:

  1. CURRENT STATE — architecture map of Summit OS as it actually is today

  2. THE AUDIT — everything from Step 4, ranked by how much it matters

  3. THE REBRAND PLAN — every file that needs to change, how you'll tokenize the
     colors, what could break, and how we roll back if I hate it

  4. THE JARVIS INTEGRATION PLAN — where the service lives, the data flow for
     each channel, what existing code we reuse, what schema changes are needed

  5. BUILD SEQUENCE — ordered work packages, each independently testable and
     shippable, with how I verify each one worked

  6. EVERYTHING YOU NEED FROM ME — this is the section I care most about. A
     numbered checklist of every single thing I have to do myself: every API key
     and exactly where to get it, every account to create, every file to export,
     every credential to find, every decision to make, every permission to grant.
     Be exhaustive. Assume I know nothing and will do exactly what you write and
     nothing more. If I have to click something in a dashboard, tell me which
     dashboard, which menu, and which button.

  7. HONEST PUSHBACK — where my plan is wrong, overcomplicated, or a bad idea.
     What I'm underestimating. What to cut from v1 to ship faster. If anything
     I've described isn't actually achievable the way I'm imagining it, say so
     directly and propose the closest real alternative. I need truth more than
     I need agreement.

  8. THE ONE THING — if I could only build one piece of this in the next week,
     what single piece would move me closest to signing more clients, and why?

═══════════════════════════════════════════════════════════════
HOW TO WORK WITH ME
═══════════════════════════════════════════════════════════════

  - Explain everything in plain English. I'm a founder, not an engineer.
  - Before installing anything global or changing anything structural, tell me
    what and why, and wait for my answer.
  - After each significant piece of work, give me one command to verify it works.
  - If you need a credential I haven't given you, stop and ask. Don't guess or
    stub it and move on.
  - Never put a secret in frontend code or anything that could get committed.
  - Work in small, reviewable, revertible commits.
  - If you're uncertain whether I want something, ask rather than assume. A
    thirty second question beats an hour of rework.

The outcome I'm paying for with my time here: I want to wake up, open Summit OS,
and in sixty seconds know exactly what my business did overnight, who needs me,
and what the highest-leverage thing I can do today is. Then I want to spend the
rest of my day on sales calls while the system handles everything else.

That's it. That's the whole goal. Build toward that.

Start by reading docs/PROJECT_JARVIS_Complete_Build.html and my codebase, then
give me the plan.
```

---

## After it responds

1. **Read `docs/SUMMIT_OS_MASTER_PLAN.md` completely** before approving anything.
2. **Work section 6 first** — the checklist of what it needs from you. Nothing proceeds until those are done.
3. **Take section 7 seriously.** You asked for pushback; if it gives you some, resist the urge to argue it down.
4. **Do the rebrand as its own commit** before the Jarvis work starts. Confirm you like the look on a live screen. Easy to revert now, painful to revert later.
5. Then continue with the sequenced prompts (Prompt 0 onward) from `JARVIS_SUMMIT_OS_PROMPTS.md`.
