# SkyBuddy AI End-to-End Audit

Audit date: 2026-08-18

## Scope

Reviewed the AI orchestrator, 14 specialist agents, deterministic and real-provider fallbacks, command planner, tool permissions, conversation memory, session boundaries, booking/seat/refund/waitlist transactions, admin analytics, 3D navigation actions, voice/avatar controls, REST APIs and responsive UI rules.

## Defects found and fixed

1. **Passenger context could default to all bookings** — assistant, bookings, waitlist and notification reads are now scoped to the server-side session identity. Public waitlist output masks names and removes email addresses.
2. **Admin data could be queried without a role check** — admin booking, waitlist, statistics, SkyAdmin, flight-update and reset APIs now require a valid server-side session with `AIRLINE_ADMIN` or `SYSTEM_ADMIN`.
3. **Login tokens were not persisted** — tokens are now SHA-256 hashed in a relational `sessions` table with expiry. Password verification remains salted `scrypt` plus timing-safe comparison.
4. **Development UI had no identity bootstrap** — a development-only demo-session endpoint supplies passenger/admin sessions; it is disabled in production.
5. **Conversation memory could cross users when a conversation ID was guessed** — memory retrieval and deletion now require both conversation ID and authenticated user email.
6. **Sensitive demo APIs trusted only the UI** — cancellation/recovery, delay, gate change, reset, preference updates and support-ticket creation now enforce confirmation server-side (`428` without confirmation).
7. **Admin and passenger confirmation buttons were incomplete** — explicit confirmation prompts/cards now precede operational and cancellation actions.
8. **Seat allocation used a read-then-write without a guarded update** — allocation now uses a conditional seat update and checks `changes === 1`; a partial unique index prevents more than one confirmed booking for a flight/seat.
9. **Recovered seat update was not checked** — seat release and re-reservation are guarded and abort the entire SQLite transaction on conflict.
10. **Payment status was marked refunded while refund status was only initiated** — cancellation now keeps payment state unchanged until refund completion; a refund record starts at `INITIATED`.
11. **Booking totals trusted the browser** — totals are calculated server-side from flight fare, fare tier, seat price, extra baggage and fixed demo taxes.
12. **Authenticated account and booking contact could diverge** — demo booking contact must match the authenticated passenger identity.
13. **Follow-up messages could overwrite a prior travel date with today** — short-term memory now preserves the date unless the new message explicitly provides today/tomorrow/weekday/ISO date.
14. **“Day after tomorrow” parsed as tomorrow** — relative-date precedence was corrected; weekday and “next Friday” parsing were added.
15. **Morning/evening preferences were parsed but not applied** — verified offer filtering now applies the requested departure window.
16. **Booking status and flight status shared the same result-column name** — database queries now return `booking_status` and `flight_status` separately.
17. **Seat recommendation action implied immediate reservation** — it now continues to verified flight selection; no seat is changed without the normal booking workflow.
18. **Gate-navigation AI action opened only the default map** — it now opens the 3D airport map and starts the guided route.
19. **SkyAdmin “high occupancy” returned only generic totals** — it now queries verified seat records and lists flights meeting the 70% threshold.
20. **Support and preference tools lacked executable confirmed paths** — both now have authenticated, confirmation-required APIs and agent-plan actions.
21. **AI could present unverified real-world data** — dynamic inventory remains labelled demo-generated; live claims come only from Amadeus responses; weather/traffic requests explicitly report unavailable providers.
22. **Failure isolation** — model-provider errors return the deterministic response; normal search, booking and navigation remain independent of AI.

## Agents implemented

- AIOrchestrator
- FlightSearchAgent
- FlightRecommendationAgent
- BookingAssistantAgent
- SeatAssistantAgent
- WaitlistAgent
- RefundAgent
- FlightMonitoringAgent
- TripPlanningAgent
- AirportNavigationAgent
- BaggageAssistantAgent
- CustomerSupportAgent
- PersonalizationAgent
- NotificationAgent
- SkyAdminAgent

## Tools and permissions

### Read-only

Flight search/details/comparison, booking lookup/history, seat map/recommendation, waitlist status/probability, refund estimate, flight status, baggage allowance, airport map/route, trip plan and preference lookup.

### Confirmation required

Seat reservation, booking creation, cancellation, refund request, add-on purchase, booking modification, preference updates and support-ticket creation.

### Admin only

Flight management and protected administrative data/actions.

The LLM has no SQL interface. Context is assembled server-side and actions use allowlisted API/service operations.

## Database and services connected

SQLite relational tables for users, sessions, airports, flights, seats, bookings, tickets, refunds, waitlist, notifications, audit logs, conversations, preferences and support tickets. Connected services include seeded/dynamic/Amadeus aviation data, booking and seat allocation, atomic cancellation/recovery, notifications, indoor route data, AI providers and browser speech services.

## Test results

- 17 unit tests: passed
- 15 required demo scenarios: passed
- Admin role-denial checks: passed
- Missing-confirmation rejection: passed
- Preference/support confirmation checks: passed
- Concurrent duplicate seat allocation: one success, one `409` — passed
- Concurrent cancellation/recovery: one success, one safe rejection — passed
- Refund calculation: ₹5,000 fare − ₹500 fee = ₹4,500 — passed
- Recovered seat ownership: exactly one confirmed owner (Rahul) — passed
- Passenger data isolation: passed
- TypeScript server validation: passed
- Frontend TypeScript/Vite production build: passed

Run:

```bash
npm test
python3 server/tests/e2e-audit.py   # requires npm run dev
npm run build
```

## Remaining limitations

- Amadeus and real-model behavior depends on external credentials, provider uptime and provider coverage. Deterministic fallbacks remain active without credentials.
- Payments are intentionally simulated; no PCI payment processor is connected.
- The development demo-session bootstrap is intentionally disabled in production. A production deployment still needs the login/registration UI wired to the now-persistent session APIs.
- Browser speech recognition support is strongest in Chrome/Edge and requires HTTPS or localhost plus microphone permission.
- Camera/video interpretation is not enabled without a configured multimodal provider and is not presented as functional.
- 3D rendering has mobile/reduced-motion fallbacks, but physical-device GPU/browser testing remains necessary before commercial deployment.
- The main frontend bundle is functional but large (~1.3 MB uncompressed); route-level lazy loading is still recommended.
- Flight payment, ticketing, check-in and legal visa/document validation require certified external production providers.
