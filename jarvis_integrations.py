"""Bounded external integrations for SummitOS JARVIS.

Every function returns observed API data or raises IntegrationUnavailable. Secrets
remain in Railway. Mutating functions are deliberately separate from reads so the
caller can require approval and idempotency before invoking them.
"""

from __future__ import annotations

import asyncio
import base64
import os
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from zoneinfo import ZoneInfo
from typing import Any

import httpx


class IntegrationUnavailable(RuntimeError):
    pass


def integration_status() -> dict[str, dict[str, Any]]:
    google = all(os.getenv(k) for k in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN"))
    slack_token = os.getenv("SLACK_BOT_TOKEN", "").strip()
    slack_channel = os.getenv("SLACK_CHANNEL_ID", "").strip()
    slack_webhook = os.getenv("SLACK_WEBHOOK_URL", "").strip()
    slack_conversation_ready = slack_token.startswith("xoxb-") and bool(slack_channel and os.getenv("SLACK_SIGNING_SECRET"))
    return {
        "summitos": {"ready": bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY")), "capabilities": ["brief", "clients", "agents", "leads"]},
        "ghl": {"ready": bool(os.getenv("GHL_PRIVATE_TOKEN") and os.getenv("GHL_LOCATION_ID")), "capabilities": ["contacts", "pipelines", "opportunity_health", "conversations"]},
        "web_research": {"ready": bool(os.getenv("FIRECRAWL_API_KEY")), "capabilities": ["search", "scrape"]},
        "google_calendar": {"ready": google, "capabilities": ["upcoming_events", "availability", "create_event"]},
        "gmail": {"ready": google, "capabilities": ["search", "read_full", "inbox_triage", "draft", "send_draft", "label", "archive", "mark_read", "trash"]},
        "google_drive": {"ready": google, "capabilities": ["search", "read"]},
        "slack": {"ready": slack_conversation_ready, "notifications_ready": slack_webhook.startswith("https://hooks.slack.com/"), "conversation_ready": slack_conversation_ready, "capabilities": ["history", "send", "channel_conversation"]},
        "telegram": {"ready": bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_ALLOWED_CHAT_IDS") and os.getenv("TELEGRAM_WEBHOOK_SECRET")), "capabilities": ["receive", "reply"]},
        "twilio": {"ready": all(os.getenv(k) for k in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_NUMBER")), "capabilities": ["inbound_sms", "outbound_sms", "inbound_call", "outbound_call"]},
        "local_computer": {"ready": True, "capabilities": ["files", "git", "processes", "approved_commands"]},
    }


async def _request_with_retry(method: str, url: str, **kwargs) -> httpx.Response:
    last: Exception | None = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=25) as client:
                response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except (httpx.HTTPError, TimeoutError) as exc:
            last = exc
            if attempt < 2:
                await asyncio.sleep(5)
    raise IntegrationUnavailable(f"API request failed after three attempts: {last.__class__.__name__ if last else 'unknown'}")


def _ghl_headers() -> dict[str, str]:
    token = os.getenv("GHL_PRIVATE_TOKEN", "")
    if not token:
        raise IntegrationUnavailable("GHL_PRIVATE_TOKEN is not configured")
    return {"Authorization": f"Bearer {token}", "Version": "2021-07-28", "Content-Type": "application/json"}


async def ghl_pipelines() -> dict:
    location = os.getenv("GHL_LOCATION_ID", "")
    response = await _request_with_retry("GET", "https://services.leadconnectorhq.com/opportunities/pipelines", headers=_ghl_headers(), params={"locationId": location})
    pipelines = response.json().get("pipelines", [])
    return {"pipelines": [{"id": p.get("id"), "name": p.get("name"), "stages": [{"id": s.get("id"), "name": s.get("name")} for s in p.get("stages", [])]} for p in pipelines]}


async def ghl_search_contacts(query: str, limit: int = 20) -> dict:
    location = os.getenv("GHL_LOCATION_ID", "")
    response = await _request_with_retry("GET", "https://services.leadconnectorhq.com/contacts/", headers=_ghl_headers(), params={"locationId": location, "query": query, "limit": min(max(limit, 1), 50)})
    contacts = response.json().get("contacts", [])
    return {"contacts": [{"id": c.get("id"), "name": c.get("contactName") or c.get("name"), "company": c.get("companyName"), "email": c.get("email"), "phone": c.get("phone"), "tags": c.get("tags", [])} for c in contacts]}


async def ghl_opportunity_health(limit: int = 100, stale_days: int = 7) -> dict:
    """Return an observed, read-only sales-pipeline health snapshot."""
    location = os.getenv("GHL_LOCATION_ID", "")
    pipelines, response = await asyncio.gather(
        ghl_pipelines(),
        _request_with_retry(
            "GET", "https://services.leadconnectorhq.com/opportunities/search",
            headers=_ghl_headers(),
            params={"location_id": location, "status": "open", "limit": min(max(limit, 1), 100)},
        ),
    )
    stage_names = {
        stage.get("id"): {"stage": stage.get("name"), "pipeline": pipe.get("name")}
        for pipe in pipelines.get("pipelines", []) for stage in pipe.get("stages", [])
    }
    now = datetime.now(timezone.utc)
    rows = []
    for opportunity in response.json().get("opportunities", []):
        changed_raw = opportunity.get("lastStageChangeAt") or opportunity.get("updatedAt") or opportunity.get("createdAt")
        age_days = None
        if changed_raw:
            try:
                age_days = (now - datetime.fromisoformat(str(changed_raw).replace("Z", "+00:00"))).days
            except ValueError:
                pass
        contact = opportunity.get("contact") or {}
        labels = stage_names.get(opportunity.get("pipelineStageId"), {})
        rows.append({
            "id": opportunity.get("id"), "name": opportunity.get("name"),
            "pipeline": labels.get("pipeline"), "stage": labels.get("stage"),
            "monetary_value": opportunity.get("monetaryValue"),
            "stage_age_days": age_days, "stale": age_days is not None and age_days >= stale_days,
            "contact": {"id": contact.get("id") or opportunity.get("contactId"), "name": contact.get("name"), "company": contact.get("companyName"), "email": contact.get("email"), "phone": contact.get("phone")},
            "updated_at": opportunity.get("updatedAt"),
        })
    stale = sorted((row for row in rows if row["stale"]), key=lambda row: row.get("stage_age_days") or 0, reverse=True)
    return {
        "status": "open", "open_count": len(rows),
        "open_value": sum(float(row.get("monetary_value") or 0) for row in rows),
        "stale_after_days": stale_days, "stale_count": len(stale),
        "stale_opportunities": stale[:25], "opportunities": rows[:50],
    }


async def prospects_without_website(limit: int = 10) -> dict:
    """Return high-signal uncontacted prospects from SummitOS, never send to them."""
    url, key = os.getenv("SUPABASE_URL", ""), os.getenv("SUPABASE_KEY", "")
    if not url or not key:
        raise IntegrationUnavailable("Supabase is not configured")
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    params = {
        "select": "id,ghl_contact_id,company_name,owner_name,phone,email,city,state,website,has_website,review_count,review_rating,outreach_sent,status,scraped_at",
        "or": "(has_website.eq.false,website.is.null,website.eq.)",
        "outreach_sent": "eq.false",
        "order": "review_count.desc.nullslast,scraped_at.desc",
        "limit": str(min(max(limit, 1), 25)),
    }
    response = await _request_with_retry("GET", f"{url}/rest/v1/scraped_businesses", headers=headers, params=params)
    return {"outreach_paused": True, "prospects": response.json()}


async def prospect_company_brief(query: str) -> dict:
    """Combine SummitOS lead data, GHL contact data, and current public research."""
    if not query.strip():
        raise IntegrationUnavailable("A company or contact name is required")
    url, key = os.getenv("SUPABASE_URL", ""), os.getenv("SUPABASE_KEY", "")
    local_rows: list[dict] = []
    if url and key:
        headers = {"apikey": key, "Authorization": f"Bearer {key}"}
        response = await _request_with_retry("GET", f"{url}/rest/v1/scraped_businesses", headers=headers, params={"select": "*", "company_name": f"ilike.*{query.strip()}*", "limit": "5"})
        local_rows = response.json()
    ghl, research = await asyncio.gather(
        ghl_search_contacts(query, 10),
        web_research(f'"{query}" roofing company owner reviews services', 6),
        return_exceptions=True,
    )
    return {
        "query": query,
        "summitos_records": local_rows,
        "ghl": {"unavailable": str(ghl)} if isinstance(ghl, Exception) else ghl,
        "public_research": {"unavailable": str(research)} if isinstance(research, Exception) else research,
        "instruction": "Separate observed facts from sales-call hypotheses. Never invent an owner, revenue, or website status.",
    }


async def web_research(query: str, limit: int = 5) -> dict:
    key = os.getenv("FIRECRAWL_API_KEY", "")
    if not key:
        raise IntegrationUnavailable("FIRECRAWL_API_KEY is not configured")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    response = await _request_with_retry("POST", "https://api.firecrawl.dev/v1/search", headers=headers, json={"query": query, "limit": min(max(limit, 1), 10)})
    payload = response.json()
    rows = payload.get("data", payload.get("results", []))
    return {"query": query, "results": [{"title": r.get("title"), "url": r.get("url"), "description": r.get("description") or r.get("markdown", "")[:800]} for r in rows]}


async def _google_access_token() -> str:
    required = (os.getenv("GOOGLE_CLIENT_ID"), os.getenv("GOOGLE_CLIENT_SECRET"), os.getenv("GOOGLE_REFRESH_TOKEN"))
    if not all(required):
        raise IntegrationUnavailable("Google offline OAuth is not connected to Railway")
    response = await _request_with_retry("POST", "https://oauth2.googleapis.com/token", data={"client_id": required[0], "client_secret": required[1], "refresh_token": required[2], "grant_type": "refresh_token"})
    return response.json()["access_token"]


async def google_oauth_status() -> dict:
    token = await _google_access_token()
    response = await _request_with_retry("GET", "https://oauth2.googleapis.com/tokeninfo", params={"access_token": token})
    granted = set(str(response.json().get("scope", "")).split())
    required = {
        "calendar": "https://www.googleapis.com/auth/calendar",
        "gmail_modify": "https://www.googleapis.com/auth/gmail.modify",
        "drive_readonly": "https://www.googleapis.com/auth/drive.readonly",
    }
    return {"granted_scopes": sorted(granted), "requirements": {name: scope in granted for name, scope in required.items()}, "missing_scopes": [scope for scope in required.values() if scope not in granted]}


async def google_calendar_upcoming(days: int = 7, limit: int = 20) -> dict:
    token = await _google_access_token()
    now = datetime.now(timezone.utc)
    response = await _request_with_retry("GET", "https://www.googleapis.com/calendar/v3/calendars/primary/events", headers={"Authorization": f"Bearer {token}"}, params={"timeMin": now.isoformat(), "timeMax": (now + timedelta(days=min(max(days, 1), 31))).isoformat(), "singleEvents": "true", "orderBy": "startTime", "maxResults": min(max(limit, 1), 50)})
    return {"events": [{"id": e.get("id"), "summary": e.get("summary"), "start": e.get("start"), "end": e.get("end"), "location": e.get("location"), "attendees": e.get("attendees", [])} for e in response.json().get("items", [])]}


async def google_calendar_availability(days: int = 5, duration_minutes: int = 30) -> dict:
    """Find business-hour openings without inventing or reserving time."""
    token = await _google_access_token()
    tz = ZoneInfo("America/New_York")
    now = datetime.now(tz)
    end = now + timedelta(days=min(max(days, 1), 14))
    response = await _request_with_retry(
        "POST", "https://www.googleapis.com/calendar/v3/freeBusy",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"timeMin": now.isoformat(), "timeMax": end.isoformat(), "timeZone": "America/New_York", "items": [{"id": "primary"}]},
    )
    busy = response.json().get("calendars", {}).get("primary", {}).get("busy", [])
    intervals = sorted((datetime.fromisoformat(x["start"].replace("Z", "+00:00")).astimezone(tz), datetime.fromisoformat(x["end"].replace("Z", "+00:00")).astimezone(tz)) for x in busy)
    slots = []
    cursor_day = now.date()
    while cursor_day <= end.date() and len(slots) < 30:
        if cursor_day.weekday() < 5:
            cursor = datetime.combine(cursor_day, datetime.min.time(), tzinfo=tz).replace(hour=9)
            day_end = cursor.replace(hour=17)
            cursor = max(cursor, now)
            for busy_start, busy_end in intervals:
                if busy_end <= cursor or busy_start >= day_end:
                    continue
                if busy_start - cursor >= timedelta(minutes=duration_minutes):
                    slots.append({"start": cursor.isoformat(), "end": (cursor + timedelta(minutes=duration_minutes)).isoformat()})
                cursor = max(cursor, busy_end)
            if day_end - cursor >= timedelta(minutes=duration_minutes):
                slots.append({"start": cursor.isoformat(), "end": (cursor + timedelta(minutes=duration_minutes)).isoformat()})
        cursor_day += timedelta(days=1)
    return {"time_zone": "America/New_York", "duration_minutes": duration_minutes, "window_days": days, "available_slots": slots[:20], "busy_periods_checked": len(intervals)}


async def google_calendar_create_event(arguments: dict) -> dict:
    """Create one explicitly approved event and return Google's receipt."""
    token = await _google_access_token()
    summary = str(arguments.get("summary", "")).strip()
    start = str(arguments.get("start", "")).strip()
    end = str(arguments.get("end", "")).strip()
    if not summary or not start or not end:
        raise IntegrationUnavailable("Calendar event requires summary, start, and end")
    event: dict[str, Any] = {
        "summary": summary,
        "description": str(arguments.get("description", ""))[:4000],
        "start": {"dateTime": start, "timeZone": arguments.get("time_zone", "America/New_York")},
        "end": {"dateTime": end, "timeZone": arguments.get("time_zone", "America/New_York")},
        "reminders": {"useDefault": False, "overrides": [{"method": "popup", "minutes": int(arguments.get("reminder_minutes", 15))}]},
    }
    if arguments.get("location"):
        event["location"] = str(arguments["location"])
    attendees = [str(email).strip() for email in arguments.get("attendees", []) if "@" in str(email)]
    if attendees:
        event["attendees"] = [{"email": email} for email in attendees]
    response = await _request_with_retry(
        "POST", "https://www.googleapis.com/calendar/v3/calendars/primary/events",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        params={"sendUpdates": "all" if attendees else "none"}, json=event,
    )
    created = response.json()
    return {"created": True, "id": created.get("id"), "summary": created.get("summary"), "start": created.get("start"), "end": created.get("end"), "html_link": created.get("htmlLink")}


async def gmail_search(query: str = "is:unread", limit: int = 10) -> dict:
    token = await _google_access_token(); headers = {"Authorization": f"Bearer {token}"}
    response = await _request_with_retry("GET", "https://gmail.googleapis.com/gmail/v1/users/me/messages", headers=headers, params={"q": query, "maxResults": min(max(limit, 1), 25)})
    items = response.json().get("messages", [])
    messages = []
    for item in items:
        detail = await _request_with_retry("GET", f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{item['id']}", headers=headers, params={"format": "metadata", "metadataHeaders": ["From", "Subject", "Date", "List-Unsubscribe", "Precedence", "Auto-Submitted"]})
        data = detail.json(); meta = {h["name"].lower(): h["value"] for h in data.get("payload", {}).get("headers", [])}
        messages.append({"id": data.get("id"), "thread_id": data.get("threadId"), "from": meta.get("from"), "subject": meta.get("subject"), "date": meta.get("date"), "snippet": data.get("snippet"), "mailing_list": bool(meta.get("list-unsubscribe")), "precedence": meta.get("precedence"), "auto_submitted": meta.get("auto-submitted")})
    return {"query": query, "messages": messages}


def _gmail_body(payload: dict) -> str:
    """Extract a bounded plain-text body from a Gmail payload."""
    candidates = []
    def walk(part: dict):
        mime = part.get("mimeType", "")
        data = (part.get("body") or {}).get("data")
        if data and mime in {"text/plain", "text/html"}:
            try:
                decoded = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace")
                candidates.append((0 if mime == "text/plain" else 1, decoded))
            except (ValueError, TypeError):
                pass
        for child in part.get("parts", []) or []:
            walk(child)
    walk(payload or {})
    if not candidates:
        return ""
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1][:20000]


async def gmail_get_message(message_id: str) -> dict:
    if not message_id:
        raise IntegrationUnavailable("A Gmail message id is required")
    token = await _google_access_token(); headers = {"Authorization": f"Bearer {token}"}
    response = await _request_with_retry("GET", f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}", headers=headers, params={"format": "full"})
    data = response.json(); meta = {h["name"].lower(): h["value"] for h in data.get("payload", {}).get("headers", [])}
    return {"id": data.get("id"), "thread_id": data.get("threadId"), "from": meta.get("from"), "to": meta.get("to"), "cc": meta.get("cc"), "subject": meta.get("subject"), "date": meta.get("date"), "labels": data.get("labelIds", []), "body": _gmail_body(data.get("payload", {})), "snippet": data.get("snippet")}


async def gmail_create_draft(arguments: dict) -> dict:
    token = await _google_access_token()
    recipient, subject, body = (str(arguments.get(k, "")).strip() for k in ("to", "subject", "body"))
    if not recipient or "@" not in recipient or not subject or not body:
        raise IntegrationUnavailable("Gmail draft requires a recipient email, subject, and body")
    message = EmailMessage(); message["To"] = recipient; message["Subject"] = subject
    if arguments.get("cc"): message["Cc"] = str(arguments["cc"])
    message.set_content(body)
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode().rstrip("=")
    response = await _request_with_retry("POST", "https://gmail.googleapis.com/gmail/v1/users/me/drafts", headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, json={"message": {"raw": raw, **({"threadId": arguments["thread_id"]} if arguments.get("thread_id") else {})}})
    created = response.json()
    return {"created": True, "draft_id": created.get("id"), "message_id": (created.get("message") or {}).get("id"), "to": recipient, "subject": subject}


async def gmail_send_draft(arguments: dict) -> dict:
    draft_id = str(arguments.get("draft_id", "")).strip()
    if not draft_id:
        raise IntegrationUnavailable("A Gmail draft id is required")
    token = await _google_access_token()
    response = await _request_with_retry("POST", "https://gmail.googleapis.com/gmail/v1/users/me/drafts/send", headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, json={"id": draft_id})
    sent = response.json(); return {"sent": True, "message_id": sent.get("id"), "thread_id": sent.get("threadId"), "labels": sent.get("labelIds", [])}


async def gmail_modify_message(arguments: dict) -> dict:
    message_id = str(arguments.get("message_id", "")).strip()
    if not message_id:
        raise IntegrationUnavailable("A Gmail message id is required")
    add = [str(x) for x in arguments.get("add_labels", [])][:20]; remove = [str(x) for x in arguments.get("remove_labels", [])][:20]
    token = await _google_access_token()
    response = await _request_with_retry("POST", f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}/modify", headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, json={"addLabelIds": add, "removeLabelIds": remove})
    updated = response.json(); return {"modified": True, "message_id": updated.get("id"), "labels": updated.get("labelIds", [])}


async def gmail_trash_message(arguments: dict) -> dict:
    message_id = str(arguments.get("message_id", "")).strip()
    if not message_id:
        raise IntegrationUnavailable("A Gmail message id is required")
    token = await _google_access_token()
    response = await _request_with_retry("POST", f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}/trash", headers={"Authorization": f"Bearer {token}"})
    return {"trashed": True, "message_id": response.json().get("id")}


async def gmail_create_label(arguments: dict) -> dict:
    name = str(arguments.get("name", "")).strip()
    if not name:
        raise IntegrationUnavailable("A Gmail label name is required")
    token = await _google_access_token()
    response = await _request_with_retry("POST", "https://gmail.googleapis.com/gmail/v1/users/me/labels", headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, json={"name": name, "labelListVisibility": "labelShow", "messageListVisibility": "show"})
    created = response.json(); return {"created": True, "label_id": created.get("id"), "name": created.get("name")}


async def slack_history(limit: int = 20) -> dict:
    token, channel = os.getenv("SLACK_BOT_TOKEN", ""), os.getenv("SLACK_CHANNEL_ID", "")
    if not token or not channel:
        raise IntegrationUnavailable("SLACK_BOT_TOKEN and SLACK_CHANNEL_ID are required")
    response = await _request_with_retry("GET", "https://slack.com/api/conversations.history", headers={"Authorization": f"Bearer {token}"}, params={"channel": channel, "limit": min(max(limit, 1), 50)})
    payload = response.json()
    if not payload.get("ok"):
        raise IntegrationUnavailable(f"Slack rejected history request: {payload.get('error', 'unknown')}")
    return {"channel_id": channel, "messages": [{"ts": m.get("ts"), "user": m.get("user"), "text": m.get("text", "")[:2000]} for m in payload.get("messages", [])]}


async def slack_send_message(arguments: dict) -> dict:
    token = os.getenv("SLACK_BOT_TOKEN", ""); channel = str(arguments.get("channel_id") or os.getenv("SLACK_CHANNEL_ID", "")).strip(); message = str(arguments.get("message", "")).strip(); thread_ts = str(arguments.get("thread_ts") or "").strip()
    webhook = os.getenv("SLACK_WEBHOOK_URL", "").strip()
    if not channel or not message or (not token and not webhook):
        raise IntegrationUnavailable("Slack bot token or webhook, channel id, and message are required")
    body = {"channel": channel, "text": message[:4000]}
    if thread_ts:
        body["thread_ts"] = thread_ts
    if token:
        response = await _request_with_retry("POST", "https://slack.com/api/chat.postMessage", headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, json=body)
        payload = response.json()
        if payload.get("ok"):
            return {"sent": True, "channel_id": payload.get("channel"), "timestamp": payload.get("ts"), "transport": "bot_token"}
        if not webhook:
            raise IntegrationUnavailable(f"Slack rejected message: {payload.get('error', 'unknown')}")
    webhook_body = {"text": message[:4000]}
    if thread_ts:
        webhook_body["thread_ts"] = thread_ts
    response = await _request_with_retry("POST", webhook, headers={"Content-Type": "application/json"}, json=webhook_body)
    if response.text.strip() != "ok":
        raise IntegrationUnavailable(f"Slack webhook rejected message: {response.text[:80] or 'unknown'}")
    return {"sent": True, "channel_id": channel, "timestamp": None, "transport": "webhook_fallback"}


async def twilio_send_sms(arguments: dict) -> dict:
    sid, auth, sender = os.getenv("TWILIO_ACCOUNT_SID", ""), os.getenv("TWILIO_AUTH_TOKEN", ""), os.getenv("TWILIO_NUMBER", "")
    destination = str(arguments.get("to", "")).strip(); message = str(arguments.get("message", "")).strip()
    allowed = {x.strip() for x in os.getenv("JARVIS_ALLOWED_SMS_RECIPIENTS", os.getenv("DAN_PHONE_NUMBER", "")).split(",") if x.strip()}
    if not sid or not auth or not sender or destination not in allowed or not message:
        raise IntegrationUnavailable("Twilio is incomplete or the destination is not allowlisted")
    response = await _request_with_retry("POST", f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json", auth=(sid, auth), data={"To": destination, "From": sender, "Body": message[:1500]})
    payload = response.json(); return {"sent": True, "message_sid": payload.get("sid"), "status": payload.get("status"), "to": destination}


async def twilio_place_call(arguments: dict) -> dict:
    """Place an outbound call that connects to the live Jarvis phone conversation loop (/jarvis/phone/twiml)."""
    sid, auth, sender = os.getenv("TWILIO_ACCOUNT_SID", ""), os.getenv("TWILIO_AUTH_TOKEN", ""), os.getenv("TWILIO_NUMBER", "")
    destination = str(arguments.get("to", "")).strip() or os.getenv("DAN_PHONE_NUMBER", "")
    allowed = {item.strip() for item in os.getenv("JARVIS_ALLOWED_CALLERS", "").split(",") if item.strip()}
    public_url = os.getenv("JARVIS_PUBLIC_URL", "").rstrip("/")
    if not sid or not auth or not sender or not public_url or destination not in allowed:
        raise IntegrationUnavailable("Twilio outbound calling is not fully configured or destination is not allowlisted")
    response = await _request_with_retry(
        "POST", f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Calls.json", auth=(sid, auth),
        data={"To": destination, "From": sender, "Url": f"{public_url}/jarvis/phone/twiml", "Method": "POST"},
    )
    payload = response.json()
    return {"status": "calling", "call_sid": payload.get("sid"), "to": destination}


async def gmail_inbox_triage(limit: int = 25) -> dict:
    """Classify unread metadata/snippets; it does not mutate the mailbox."""
    result = await gmail_search("is:unread newer_than:30d", limit)
    buckets = {"reply_now": [], "revenue_or_client": [], "calendar_or_meeting": [], "newsletter_or_automated": [], "other": []}
    for message in result.get("messages", []):
        text = " ".join(str(message.get(k) or "") for k in ("from", "subject", "snippet")).casefold()
        automated_headers = message.get("mailing_list") or str(message.get("precedence") or "").casefold() in {"bulk", "list", "junk"} or str(message.get("auto_submitted") or "").casefold() not in {"", "no"}
        if automated_headers or any(term in text for term in ("unsubscribe", "newsletter", "no-reply", "noreply", "notification", "webinar", "limited time", "special offer", "sale ends", "digest", "your weekly", "free training")):
            bucket = "newsletter_or_automated"
        elif any(term in text for term in ("meeting", "calendar", "invite", "appointment", "reschedule")):
            bucket = "calendar_or_meeting"
        elif any(term in text for term in ("invoice", "payment", "client", "proposal", "contract", "roof", "lead", "demo")):
            bucket = "revenue_or_client"
        elif any(term in text for term in ("question", "re:", "following up", "can you", "could you")):
            bucket = "reply_now"
        else:
            bucket = "other"
        buckets[bucket].append(message)
    return {"query": result["query"], "unread_count_sampled": len(result.get("messages", [])), "buckets": buckets, "note": "Priority labels are deterministic suggestions based on message metadata and snippets; no email was changed."}


async def google_drive_search(query: str, limit: int = 10) -> dict:
    token = await _google_access_token()
    safe_query = query.replace("'", "\\'").strip()
    params = {
        "q": f"trashed = false and fullText contains '{safe_query}'" if safe_query else "trashed = false",
        "pageSize": min(max(limit, 1), 25),
        "orderBy": "modifiedTime desc",
        "fields": "files(id,name,mimeType,modifiedTime,webViewLink,owners(displayName,emailAddress))",
    }
    response = await _request_with_retry("GET", "https://www.googleapis.com/drive/v3/files", headers={"Authorization": f"Bearer {token}"}, params=params)
    return {"query": query, "files": response.json().get("files", [])}


async def meeting_prep(query: str = "next meeting") -> dict:
    """Assemble one observed meeting dossier across the connected business systems."""
    calendar = await google_calendar_upcoming(30, 50)
    events = calendar.get("events", [])
    needle = query.casefold().replace("meeting brief", "").replace("meeting prep", "").strip(" :,.?")
    generic = not needle or needle in {"next", "next meeting", "my next meeting", "upcoming"}
    selected = None
    if generic:
        eligible = [event for event in events if not any(isinstance(a, dict) and a.get("self") and a.get("responseStatus") == "declined" for a in event.get("attendees", []))]
        selected = eligible[0] if eligible else None
    else:
        selected = next((event for event in events if needle in str(event.get("summary", "")).casefold() or any(needle in str(a).casefold() for a in event.get("attendees", []))), None)
    if not selected:
        return {"query": query, "meeting": None, "calendar_events_checked": len(events), "message": "No matching upcoming calendar event was found."}
    attendee_emails = [a.get("email") for a in selected.get("attendees", []) if isinstance(a, dict) and a.get("email")]
    search_term = str(selected.get("summary") or needle or "").strip()
    gmail_query = f'newer_than:2y "{search_term}"' if search_term else "newer_than:30d"
    ghl_query = attendee_emails[0] if attendee_emails else search_term
    results = await asyncio.gather(
        gmail_search(gmail_query, 12),
        ghl_search_contacts(ghl_query, 10),
        google_drive_search(search_term, 10),
        prospect_company_brief(search_term),
        return_exceptions=True,
    )
    labels = ("gmail", "ghl", "drive", "company_intelligence")
    dossier = {label: ({"unavailable": str(value)} if isinstance(value, Exception) else value) for label, value in zip(labels, results)}
    return {
        "meeting": selected,
        "attendee_emails": attendee_emails,
        **dossier,
        "briefing_requirements": ["meeting objective", "relationship history", "open promises", "likely needs", "talking points", "objections", "next best action"],
    }


async def daily_executive_inputs() -> dict:
    """Return observed inputs for a revenue-first daily briefing."""
    results = await asyncio.gather(
        google_calendar_upcoming(2, 25),
        gmail_inbox_triage(25),
        prospects_without_website(10),
        ghl_opportunity_health(100, 7),
        return_exceptions=True,
    )
    labels = ("calendar", "inbox_triage", "no_website_prospects", "pipeline_health")
    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "outreach_paused": True,
        **{label: ({"unavailable": str(value)} if isinstance(value, Exception) else value) for label, value in zip(labels, results)},
    }


READ_TOOLS = {
    "integrations_status": lambda args: integration_status(),
    "google_oauth_status": lambda args: google_oauth_status(),
    "ghl_pipelines": lambda args: ghl_pipelines(),
    "ghl_search_contacts": lambda args: ghl_search_contacts(str(args.get("query", "")), int(args.get("limit", 20))),
    "ghl_opportunity_health": lambda args: ghl_opportunity_health(int(args.get("limit", 100)), int(args.get("stale_days", 7))),
    "prospects_without_website": lambda args: prospects_without_website(int(args.get("limit", 10))),
    "prospect_company_brief": lambda args: prospect_company_brief(str(args.get("query", ""))),
    "web_research": lambda args: web_research(str(args.get("query", "")), int(args.get("limit", 5))),
    "calendar_upcoming": lambda args: google_calendar_upcoming(int(args.get("days", 7)), int(args.get("limit", 20))),
    "calendar_availability": lambda args: google_calendar_availability(int(args.get("days", 5)), int(args.get("duration_minutes", 30))),
    "gmail_search": lambda args: gmail_search(str(args.get("query", "is:unread")), int(args.get("limit", 10))),
    "gmail_get_message": lambda args: gmail_get_message(str(args.get("message_id", ""))),
    "gmail_inbox_triage": lambda args: gmail_inbox_triage(int(args.get("limit", 25))),
    "slack_history": lambda args: slack_history(int(args.get("limit", 20))),
    "drive_search": lambda args: google_drive_search(str(args.get("query", "")), int(args.get("limit", 10))),
    "meeting_prep": lambda args: meeting_prep(str(args.get("query", "next meeting"))),
    "daily_executive_inputs": lambda args: daily_executive_inputs(),
}

WRITE_TOOLS = {
    "calendar_create_event": google_calendar_create_event,
    "gmail_create_draft": gmail_create_draft,
    "gmail_send_draft": gmail_send_draft,
    "gmail_modify_message": gmail_modify_message,
    "gmail_trash_message": gmail_trash_message,
    "gmail_create_label": gmail_create_label,
    "slack_send_message": slack_send_message,
    "twilio_send_sms": twilio_send_sms,
    "twilio_place_call": twilio_place_call,
}


async def execute_read_tool(name: str, arguments: dict) -> Any:
    fn = READ_TOOLS.get(name)
    if not fn:
        raise IntegrationUnavailable(f"Unknown integration tool: {name}")
    result = fn(arguments)
    return await result if hasattr(result, "__await__") else result


async def execute_write_tool(name: str, arguments: dict) -> Any:
    fn = WRITE_TOOLS.get(name)
    if not fn:
        raise IntegrationUnavailable(f"Unknown mutating integration tool: {name}")
    result = fn(arguments)
    return await result if hasattr(result, "__await__") else result
