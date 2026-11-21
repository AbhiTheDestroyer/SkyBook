# SkyBook My Journey — End-to-End QA Audit

Audit date: 2026-08-18

## Outcome

The complete BOOKING → MY JOURNEY → CHECK-IN → BOARDING PASS → SEAT → BAGGAGE → GATE → AIRPORT NAVIGATION → BOARDING → DEPARTURE → IN FLIGHT → ARRIVAL → COMPLETED lifecycle passed.

## Defects found and fixed

1. **Initial journey creation used 13 values for 12 segment columns.** Corrected the insert and verified fresh journey creation after reset.
2. **Gate `24` was not normalized to the airport graph's `B24`.** Journey creation and synchronization now normalize numeric gates from current terminal data.
3. **Normalized B24 could repeatedly compare against raw flight gate 24 and create stale duplicate gate events.** Current flight gate is normalized before comparison and snapshot update.
4. **Check-in override could not be found during state synchronization.** Flight ID/payment fields are now passed into the state engine.
5. **Payment PENDING and FAILED were ignored by journey state.** Added PAYMENT_PENDING and PAYMENT_FAILED states and corresponding next actions.
6. **Flight/gate/terminal changes created journey events but not user notifications.** Synchronization now emits deduplicated, delivery-tracked notifications.
7. **A12 → B24 consistency was not explicitly guaranteed.** Added an end-to-end consistency test across My Journey details, next action, notifications, Airport Navigator and SkyBuddy; all resolve B24/T2.
8. **Multi-seat bookings created one passenger with a comma-separated seat.** Journey creation now creates one passenger record per normalized booking seat.
9. **Seat change released every seat and assigned the new seat to every passenger.** It now changes only the selected/default passenger, updates only that seat ownership, and recomputes the booking's aggregate seat list transactionally.
10. **Additional baggage updated booking total but not the payment aggregate.** Both records now update together and a baggage event is stored.
11. **Boarding Pass action was available before check-in.** It is now disabled until an actual passenger check-in record is CHECKED_IN; the ticket remains available.
12. **Relevant Offers section was only a generic link.** Journey aggregation now runs the existing OfferService against the current user/flight/cabin and shows only eligible active offers with a revalidation warning.
13. **SkyBuddy lacked a journey-specific agent.** JourneyAgent now answers using the authenticated aggregate, verified flight/gate/seat/check-in/payment and backend next-action result.
14. **Checked-in next action omitted the changed gate.** Boarding-pass/boarding next actions now carry current gate context.
15. **Multi-passenger journey behavior had no dedicated demonstration.** Added a two-passenger booking with distinct normalized seats and passengers.
16. **Multi-segment behavior had no backend demo.** Added DEL→DXB and DXB→LHR segments with a 2h15 layover event.
17. **Completion depended on wall-clock arrival.** Added a controlled admin completion operation that updates booking/journey state and timeline.
18. **Share request could include unsafe fields.** Server whitelists only flight, route, departure and status; payment/document fields are removed.
19. **Documents could imply verification.** The prototype stores only `NOT_VERIFIED` status and a masked “Not stored” reference; raw files are never persisted.
20. **My Journey relied on old booking cards.** Replaced with database journey APIs, state-driven cards/details, controlled polling, offline cache, search/history filters, tasks, alerts and functional action bar.

## Lifecycle verification

- Booking creates exactly one journey: PASS
- Owned journey dashboard/details: PASS
- Check-in closed reason: PASS
- Check-in open and completion: PASS
- Boarding pass readiness: PASS
- Seat inventory change: PASS
- Baggage/payment synchronization: PASS
- Gate/terminal change: PASS
- Airport navigation destination: PASS
- Delay alert: PASS
- Boarding next action: PASS
- Departure → IN_FLIGHT: PASS
- Arrival → LANDED: PASS
- Completion → history: PASS

## Additional scenario verification

1. Flight delay — PASS
2. Gate change — PASS
3. Terminal change — PASS
4. Flight cancellation — PASS
5. Payment pending — PASS
6. Payment failure — PASS
7. Refund INITIATED and amount — PASS
8. Waitlist promotion — PASS
9. Multi-passenger/distinct seats — PASS
10. Multi-segment journey — PASS
11. Layover event — PASS
12. Seat change — PASS
13. Baggage — PASS
14. Eligible Offers — PASS
15. SkyBuddy JourneyAgent — PASS
16. Airport Navigator — PASS
17. Existing 3D seat inventory integration — PASS
18. Journey notifications — PASS
19. Completed/cancelled history filters — PASS
20. Personal checklist — PASS
21. Mobile layout rules — PASS
22. Desktop two-column details — PASS
23. Semantic buttons/status/text fallback/reduced motion — PASS
24. Session authentication — PASS
25. Cross-user journey access returns 404 — PASS

## Critical consistency rules

- **ONE USER → ONLY THEIR JOURNEYS:** server session ownership enforced.
- **ONE BOOKING → CORRECT JOURNEY:** unique `journeys.booking_id` plus idempotent sync.
- **ONE SEGMENT → CORRECT STATUS:** segment snapshot synchronized from its flight.
- **ONE SEAT → CORRECT PASSENGER:** normalized `booking_seats` plus passenger-scoped seat updates.
- **ONE GATE → CURRENT FLIGHT DATA:** normalization and snapshot change events.

A12 → B24 was verified across:

- My Journey dashboard/detail
- Segment flight details
- Next action
- Notification center
- Airport Navigator gate node
- SkyBuddy response
- Boarding-pass data path

## Security and privacy

- Journey APIs use authenticated server identity; frontend user/booking IDs are not trusted.
- Other users receive 404 for journey details.
- Seat, baggage, check-in and cancellation changes require backend confirmation/business logic.
- Share fields are allowlisted.
- Raw travel documents and payment credentials are never stored/exposed.
- Admin analytics are aggregate only.
- AI receives an authorized journey aggregate and has no SQL/state-transition tool.

## Full regression

- 24/24 unit tests passed
- Core booking/recovery E2E passed
- Offers E2E passed
- Navigation E2E passed
- Smart Waitlist E2E passed
- My Journey E2E passed
- Server TypeScript validation passed
- Frontend TypeScript/Vite production build passed

## Remaining production constraints

- Flight/check-in/boarding data remains explicitly demo data without airline DCS/live provider integration.
- Baggage tracking remains unavailable rather than fabricated.
- Browser print provides the journey summary; production PDF generation is not connected.
- Controlled polling should be replaced by SSE/WebSockets at production scale.
- Physical mobile/device testing and route-level code splitting remain recommended.
