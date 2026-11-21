# SkyBook My Journey — Functional Implementation

## Purpose

My Journey is an authenticated travel aggregate and command center. It is not a static dashboard: every journey is synchronized from existing booking, flight, seat, ticket, payment, refund, baggage, waitlist, offer, navigation and notification data.

## Data model

- `journeys`
- `journey_segments`
- `journey_passengers`
- `journey_events`
- `journey_tasks`
- `journey_documents`
- `journey_baggage`
- `journey_demo_controls`
- `journey_analytics`
- `journey_shares`

Journeys are created idempotently from owned bookings. Segment gate, terminal and status snapshots are compared with current flight records; changes generate events before the snapshot updates.

## State model

Supported derived states include UPCOMING, CHECK_IN_OPEN, CHECKED_IN, BOARDING, DELAYED, IN_FLIGHT, LANDED, COMPLETED and CANCELLED. State comes from booking status, flight status, check-in record and configured demo controls—not UI assumptions.

The timeline is generated from the state machine and immutable events. Only reached states are marked complete.

## Functional capabilities

- Upcoming, ongoing, completed, cancelled and waitlisted views
- Search by PNR, journey reference, flight, route and destination
- Nearest departure sorting
- Details, segments, passengers, seats, ticket, payment, baggage and refund
- Check-in eligibility with 24-hour policy or admin demo override
- Check-in completion and boarding-pass readiness
- Existing seat inventory/transaction-based seat changes
- Additional baggage and synchronized demo payment total
- Dynamic next-best action
- Journey readiness and system checklist
- Personal tasks with completion state
- Privacy-safe document status; raw sensitive documents are not stored
- Gate/terminal/delay/boarding/departure/arrival alerts
- Airport Navigator launch with current flight gate
- Smart Waitlist cards and promotion-required state
- Offers link with checkout revalidation
- SkyBuddy JourneyAgent grounding
- Privacy-controlled share fields
- Print/download browser summary
- Offline cache with last-updated label
- 15-second controlled polling only while visible
- Multi-segment DEL→DXB→LHR demo with 2h15 layover event

## Security

All journey APIs resolve identity from the hashed server session. Journey ID, booking ID and user email from the frontend are never trusted for ownership. Cross-user detail access returns 404. Share views whitelist flight, route, departure and status and exclude payment/documents/passport data.

Seat changes, check-in, baggage, cancellation, state changes and sharing use backend services. Sensitive/destructive operations require confirmation. SkyBuddy receives an already-authorized journey aggregate and has no SQL or state-transition authority.

## API

- `GET /api/journeys`
- `GET /api/journeys/:id`
- Timeline, status, next-action, passengers, segments and alerts subresources
- `POST /api/journeys/:id/checkin`
- Task create/update
- Confirmed seat change and baggage purchase
- Privacy-safe share generation
- Admin journey analytics and controlled demo state/check-in controls

## Tested workflow

1. Upcoming trip appears
2. Complete owned details load
3. Check-in unavailable reason is correct
4. Check-in window opens and next action changes
5. Check-in completes and boarding pass becomes ready
6. Personal checklist persists
7. Seat change updates inventory, booking ownership and passenger
8. Baggage purchase updates payment total
9. Gate/terminal B24/T2 → A12/T1 update creates alerts
10. Airport Navigator resolves A12
11. Delay alert appears
12. Boarding changes next action
13. Departure maps to IN_FLIGHT
14. Arrival maps to LANDED
15. Completion moves the journey to history
16. Privacy-safe sharing filters payment fields
17. SkyBuddy JourneyAgent uses verified context
18. Multi-segment journey/layover renders
19. Waitlist and promotion appear in My Journey
20. Cancellation shows refund INITIATED
21. Admin analytics aggregate correctly
22. Mobile/offline/action integrations are present

## Regression status

- Unit tests pass
- Core booking/recovery E2E passes
- Offers E2E passes
- Airport Navigation E2E passes
- Smart Waitlist E2E passes
- My Journey E2E passes
- Server and frontend TypeScript pass
- Production Vite build passes

## Production constraints

- Flight status remains seeded/demo unless a live provider is configured.
- Check-in and boarding pass are demonstration records, not airline DCS credentials.
- Baggage tracking reports unavailable rather than inventing location.
- Raw passports/visas are intentionally not stored.
- Browser print is used for summary output; a production PDF service can replace it.
- Production real-time delivery should use SSE/WebSockets instead of controlled polling.
- Route-level lazy loading is still recommended for the large frontend bundle.
