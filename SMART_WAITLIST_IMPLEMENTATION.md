# SkyBook Smart Waitlist — Functional Implementation

## Architecture

```text
Passenger / SkyBuddy / Admin
             ↓
Authenticated waitlist APIs
             ↓
Eligibility + FIFO priority + probability services
             ↓
Transactional matching / promotion service
             ↓
Seat hold → explicit payment → booking/ticket
             ↓
Notifications, events, analytics and queue update
```

AI is not in the allocation path.

## Deterministic business rules

Candidates are considered by:

1. ACTIVE status
2. Valid stored payment/fare authorization
3. Same flight and cabin
4. Required seat count available
5. Required fare ≤ maximum authorized fare
6. FIFO `joined_at`, then stable entry ID

No sensitive passenger attributes participate in priority.

## Data model

- `waitlist_entries`
- `waitlist_promotions`
- `waitlist_events`
- `waitlist_config`
- Existing users, flights, seats, bookings, payments, tickets, refunds, offers and notifications

Entry states include ACTIVE, PAYMENT_PENDING, PAYMENT_FAILED, CONFIRMED, DECLINED, EXPIRED and CANCELLED. Promotion states include PENDING, CONFIRMED, PAYMENT_FAILED, DECLINED and EXPIRED.

## Transaction safety

Cancellation, refund creation, seat release and matching execute in one SQLite transaction. Promotion confirmation verifies the server-controlled deadline and HELD seat, revalidates the optional promo, records the final payment, creates booking/ticket, assigns the seat, confirms the entry and writes events atomically.

Protections:

- Conditional `AVAILABLE → HELD → OCCUPIED` updates
- Unique idempotency key per matching event
- Unique confirmed flight/seat index
- Unique active user/flight waitlist index
- Unique promotion/booking redemption
- Repeated confirmation cannot create another booking/payment
- Group requests are not split unless `allowPartial` was explicitly enabled

## Promotion workflow

A promotion holds seats for 15 server-controlled minutes. The passenger must explicitly confirm the simulated payment. Decline, timeout or configured payment failure releases the hold and runs the next deterministic match. Automatic expiration is evaluated server-side on controlled status polling.

Optional eligible offers are shown as potential savings but never silently applied. If selected, the offer is revalidated at confirmation and the backend recalculates the final payment.

## Exact demo

SK102 is reset to five occupied seats:

- Passenger A — 11A
- Passenger B — 11B
- Passenger C — 12A
- Passenger D — 12B
- Passenger E — 13A

FIFO queue:

- #1 Passenger F — ₹6,000
- #2 Passenger G — ₹5,500
- #3 Passenger H — ₹7,000

Passenger A cancellation creates a ₹4,500 refund and a 15-minute hold on 11A for Passenger F. Confirmation creates payment, booking, PNR, ticket and notification; Passenger G becomes #1.

## UI

- Sold-out flight Join Waitlist action
- Fare authorization modal
- Passenger count and seat preference
- Optional partial-confirmation consent
- Active waitlist cards
- Anonymous FIFO visualization
- Real position and queue progress
- Explainable probability factors and guarantee disclaimer
- Update fare and leave confirmation
- Promotion countdown and price breakdown
- Apply eligible offer explicitly
- Confirm/decline/payment-failure controls
- 3D held-seat preview
- Immutable event timeline
- Ticket and airport-navigation actions
- Mobile bottom-sheet details
- Controlled 15-second visible-page refresh

## Admin

Role-protected admin APIs/dashboard provide current queues, promotion/event history, failures, controlled retry, deterministic processing and analytics. Manual actions call service methods and write events; they do not edit seat ownership or queue position directly.

Analytics include joins, active/confirmed/cancelled/payment-failed entries, average probability, average queue length, confirmation rate, promotion success, payment failure, response time, waitlisted routes and recovered revenue.

## Verification

`server/tests/smart-waitlist-e2e.py` validates:

- Join, duplicate prevention, leave and reorder
- Eligibility and fare authorization confirmation
- Probability bounds and explanation
- Cancellation/refund/seat release
- FIFO selection and seat hold
- Promotion/payment/booking/ticket
- Offer revalidation and final amount
- Idempotency and race handling
- Promotion timeout and next passenger
- Payment failure and next passenger
- Fare-limit skip with audit explanation
- Default group no-split behavior
- Explicit partial confirmation with remainder entry
- Simultaneous seats and queue progression
- Flight cancellation, schedule and gate events
- Notifications, SkyBuddy, 3D preview and admin analytics
- Passenger/admin authorization boundaries

Final regression:

- 24/24 unit tests pass
- Core booking/waitlist recovery E2E passes
- Offers E2E passes
- Navigation E2E passes
- Smart Waitlist E2E passes
- TypeScript validation and production build pass

## Production limitations

- Payment remains simulated; real authorization/charge capture needs a PCI-compliant provider.
- Notification delivery records support PENDING/SENT/FAILED semantics, but real email/SMS/push adapters are not connected.
- Real historical cancellation/no-show data is unavailable; probability is clearly labelled `SKYBOOK_DEMO_V1` and never reaches 100%.
- Production event delivery should use SSE/WebSockets; this prototype uses controlled visible-page polling.
- Physical mobile/browser testing remains necessary before commercial deployment.
