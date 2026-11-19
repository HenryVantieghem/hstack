---
name: voice-agent-eu
description: Build a business phone receptionist or multilingual voice agent for the EU, including Belgian, Dutch and French callers. Choose where recordings, transcripts, speech and model processing run. Test a SIP handoff with a regional deployment.
metadata:
  related: "voice-agent-us"
---

# Build an EU voice agent

Use one language and one business outcome for the first phone call. A useful pilot is an inbound service desk that routes a caller to a person or records a callback request.

## First conversation

Read the brief, then ask only the questions it leaves open. Give the operator concrete choices:

- “After a good call, what should exist, and where should your team see it? An appointment in your calendar, a ticket in your CRM, or something else?”
- “Where do you want the call data to live? We can keep only the outcome in your existing system, use a database you control, or use the voice provider’s storage if its terms fit. Which parts can we keep: audio, transcript, summary, phone number? For how long?”
- “What phone system do you already pay for, and who should get the call if the AI can’t finish?”

Ask whether the location rule covers storage alone or every live processing step. If the operator has to ask IT, build the synthetic test path and leave the production geography decision open.

## Build and verify

1. **Define the boundary with the operator.** Ask separately where data may be stored and where live audio, speech recognition, synthesis and model inference may run. Write down the permitted countries, any restrictions on support access, approved processors, retention and deletion owner. Draw the path from caller to carrier, SIP service, worker, speech and model endpoints, destination system, backups and logs. For each hop record purpose, fields, location, contractual evidence and outstanding questions. Use synthetic callers until a route handling personal data meets the agreed boundary.
2. **Resolve country-specific questions.** Identify controller and processors, lawful basis, caller notices, recording rules, processor agreements, transfer safeguards where applicable, and whether the use calls for an impact assessment. Consider AI interaction disclosure at first contact and national marketing rules for outbound calls. Treat these as design inputs for the operator and its adviser. [GDPR, especially Articles 5, 6, 13, 28, 35 and Chapter V](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng) · [AI Act, Article 50](https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng)
3. **Choose and document the stack.** Deploy LiveKit server, SIP service, Redis and an Agents worker on infrastructure within the allowed geography. Select a carrier that can document signaling, media routing, failover and call-detail retention. Match the Azure Speech resource, endpoint, language and voice to the location and feature. Check the Azure model deployment type as well as the resource region. The EU Data Zone can include EFTA countries. Record model availability and permitted failover before choosing it for a member-state-only requirement. Retell currently reports operating outside the EU. Recheck provider statements for each new deployment. [LiveKit SIP](https://docs.livekit.io/transport/self-hosting/sip-server/) · [Azure Speech regions](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/regions) · [Azure model processing locations](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/deployment-types) · [Retell processing statement](https://docs.retellai.com/general/compliance)
4. **Connect the call.** Route a test number to the SIP trunk, configure the inbound trunk and dispatch rule, and have the named worker join each new call room. Connect speech recognition, the conversation model and synthesis to the selected endpoints. Introduce the AI assistant in the caller's language and confirm names, numbers and requested actions. Add a human transfer and a callback route for an unanswered desk. Permit only approved endpoints and configure a human fallback if a required provider is unavailable. Scope destination credentials and deduplicate retried writes.
5. **Prove the route and handoff.** Dial from an ordinary handset. Have a fluent tester interrupt, spell a name and request a person. Verify two-way audio, transfer pickup, unanswered-transfer handling and the synthetic record in the destination. Disable a test speech endpoint and confirm the agreed fallback. Inspect endpoint configuration, regional deployment type and observed connections alongside carrier and provider evidence. Network traces alone cannot establish a vendor’s internal processing location. Check expiry or deletion of a synthetic record in each retained store; mark any timed expiry still pending.
6. **Run a bounded pilot.** Name an operator, pilot hours, traffic and cost ceilings, maximum response delay, review date and rollback trigger. Test routing the number back to the staffed desk. Hand over the service map, provider settings, redacted call results, retention evidence, recovery instructions and unresolved location questions. State which paths were verified with a real call.

**Try it:** “Use voice-agent-eu for a French-language inbound repair desk. Processing is restricted to France, callers may request a human, and audio retention is disabled. Identify any unverified provider location before handling personal data.”
