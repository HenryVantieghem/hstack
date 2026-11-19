---
name: voice-agent-us
description: Build and pilot a US phone agent on Retell, from storage and call-direction discovery to a verified human transfer and rollback.
---

# Build a US voice agent

Start with one job a caller can complete and one person who can take over. For example, an after-hours repair line can collect a callback request and transfer an urgent call to the duty desk.

## First conversation

Read the brief, then ask only the questions it leaves open. Give the operator concrete choices:

- “After a good call, what should exist, and where should your team see it? An appointment in your calendar, a ticket in your CRM, or something else?”
- “Where do you want the call data to live? We can keep only the outcome in your existing system, use a database you control, or use the voice provider’s storage if its terms fit. Which parts can we keep: audio, transcript, summary, phone number? For how long?”
- “What phone system do you already pay for, and who should get the call if the AI can’t finish?”

Start with Retell for the managed voice layer. If the business already owns a Twilio or Telnyx number, compare bringing that number via SIP with using a dedicated pilot number. If the business needs to operate its own media path, evaluate LiveKit and a SIP trunk. Carry the same conversation tests across providers. [Twilio on Retell](https://docs.retellai.com/deploy/twilio) · [Telnyx on Retell](https://docs.retellai.com/deploy/telnyx) · [LiveKit SIP](https://docs.livekit.io/transport/self-hosting/sip-server/)

## Build and verify

1. **Agree on the call.** Capture inbound or outbound, states served, operating hours and time zone, languages, caller intent, transfer number, destination system and pilot owner. Ask which data may be processed, which may be stored, where, for how long, and who can read it. Include audio, transcripts, tool payloads, webhook deliveries and backups. Record choices in the project brief.
2. **Set the operating rules.** Have the operator resolve applicable recording, disclosure and outbound rules for the jurisdictions and purpose. For outbound calls, specify the evidence that makes each number eligible, time window, suppression check and opt-out path. Start with owned test numbers. Federal artificial-voice call restrictions vary by purpose and recipient. Use this workflow as engineering guidance and have qualified counsel resolve legal questions. [47 CFR § 64.1200](https://www.ecfr.gov/current/title-47/chapter-I/subchapter-B/part-64/subpart-L/section-64.1200)
3. **Build a Retell draft.** Configure language, voice, interruption handling and business hours. Introduce the business and AI assistant, ask one question at a time, confirm critical details and offer a person. Add a transfer destination and a callback branch for busy or closed lines. Give each external action a narrow schema, server-side validation and a stable operation ID so retries create one record. Acknowledge success only after the destination confirms it.
4. **Wire the test line.** Bind the published test version to an inbound test number in Retell or connect a supported carrier. For outbound trials, use the authorized caller ID and an allowlist of testers. Configure retention and data storage on the agent before placing the first call. Check which fields also reach your own systems, verify webhook signatures, and restrict recording access if recording is enabled. [Retell privacy and agreements](https://docs.retellai.com/general/compliance) · [Retention settings](https://docs.retellai.com/accounts/data-retention)
5. **Verify the whole call.** Run scripted calls for a successful request, interruption, ambiguous name, silence, request for a person, unavailable desk and failed destination write. Repeat a delivery to verify deduplication. Dial the actual test number, have a teammate answer the transfer and read the synthetic callback request from the destination. Where outbound is enabled, opt a tester out and verify that the next attempt is suppressed. Record scenario, expected outcome, actual outcome and redacted evidence.
6. **Pilot and hand over.** Agree on traffic and cost caps, supported hours, acceptable delay and the failure rate that ends the pilot. Keep the previous phone route ready. Demonstrate restoring that route with a test call. Give the operator the version, routing controls, dashboard, escalation contact and results. Report completion only for calls and destination actions actually observed.

**Try it:** “Use voice-agent-us to build an inbound Retell callback line for a bicycle shop. The manager handles transfers, recordings are disabled, and testers use fictional names.”
