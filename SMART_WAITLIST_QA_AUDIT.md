# SkyBook Smart Waitlist — End-to-End QA Audit

Audit date: 2026-08-18

## Outcome

The complete FULL FLIGHT → JOIN → FIFO QUEUE → CANCELLATION/REFUND → SEAT RELEASE → MATCH → HOLD → PROMOTION → PAYMENT → BOOKING/TICKET → ASSIGNMENT → NOTIFICATION → QUEUE UPDATE workflow passed.

The two primary database invariants passed under sequential and concurrent execution:

```text
ONE SEAT → ONE ACTIVE BOOKING → ONE PASSENGER
ONE PROMOTION → AT MOST ONE SUCCESSFUL CONFIRMATION
```

## Defects found and fixed

1. **Individual seat ownership was represented only by `bookings.seat`.** Multi-seat values such as `11A,11B` could not be protected by the existing unique index. Added `booking_seats` with a partial unique index on `(flight_id, seat_label) WHERE status='ACTIVE'`. All normal, seeded, legacy-recovery and Smart Waitlist booking paths now maintain this table.
2. **Cancellation did not release normalized booking-seat ownership.** Cancellation now marks the corresponding `booking_seats` rows RELEASED in the same transaction before matching.
3. **Promotion confirmation checked HELD state but did not verify final update count.** Every `HELD → OCCUPIED` transition now requires exactly one changed row or the complete transaction rolls back.
4. **Expired confirmation could roll back its own expiration.** Expiration was previously invoked inside a transaction that then threw. Deadline validation now happens before the confirmation transaction; expiration and next-passenger matching commit independently.
5. **Flight cancellation could leave HELD seats behind.** All pending promotions are expired and their seat holds released before active entries close. No HELD seat survives flight cancellation.
6. **Flight schedule changes wrote events but did not run expiration revalidation.** The server now runs waitlist eligibility/flight-time expiration after schedule updates.
7. **Demo simultaneous seat release changed seat state without cancelling its booking.** The controlled demo helper now cancels each owning booking, releases normalized ownership, creates refund records, releases inventory and only then invokes matching.
8. **Payment failure released the seat but did not continue matching.** The configured RELEASE_AND_NEXT policy now updates queue positions and starts the next eligible promotion atomically.
9. **Promotion and payment duplication needed stronger database enforcement.** Added a unique promotion booking index; payments already enforce one row per booking. Confirmation status, seat ownership and transaction checks provide additional idempotency.
10. **FIFO demo join timestamps were in the future relative to server UTC.** Demo F/G/H timestamps are now generated immediately before setup so later joiners receive correct positions.
11. **Queue denominator mixed active/pending entries incorrectly.** Active passengers see active queue size; a PAYMENT_PENDING passenger sees the active queue plus the held promotion.
12. **Group requests had no safe partial flow.** Default remains all-or-nothing. If partial confirmation was explicitly enabled, available seats are held, the user confirms payment, and the remaining passenger count is inserted as a new active FIFO entry after the original confirms.
13. **Optional Offers were not connected to promotion payment.** Matching stores only a potential eligible offer. The passenger must select it; confirmation revalidates eligibility and recalculates payment/redemption server-side.
14. **The boarding pass remained hard-coded after a waitlist confirmation.** Confirmed waitlist PNR, passenger, route, terminal, gate and seats are saved to the offline-ready dynamic boarding pass.
15. **3D seat integration showed text only.** Promotion details now render a React Three Fiber cabin preview with HELD seats highlighted. It is view-only; reservation remains backend controlled.
16. **Promotion countdown reached 00:00 while Confirm remained enabled.** The action disables at zero and server deadline validation remains authoritative.
17. **Notification delivery state stayed unspecified.** Successful in-app waitlist notifications now record `SENT` with an attempt count; external adapters remain independently retryable.
18. **Probability changes were stored but significant changes did not notify.** Changes of at least 10 points now create a clear non-guaranteed notification.
19. **SkyBuddy did not understand “Did I get the seat?” and returned generic estimates for confirmed users.** Waitlist intent coverage and status-specific responses were added. Confirmed and payment-failed states are explained from database data.
20. **Smart Waitlist AI tools required an explicit non-allocation audit.** WaitlistAgent exposes only status/probability tools; tests assert it has no reserve, booking or cancellation tool.
21. **General demo reset failed after waitlist configuration was added.** `waitlist_config` is now removed before flight rows, preserving foreign-key order and restoring all legacy/core tests.
22. **Controlled polling did not refresh selected promotion details.** Visible-page polling now refreshes own entries every 15 seconds and the selected detail/promotion independently every 15 seconds.
23. **Sold-out seeded SK102 was hidden by dynamic offer generation when a date was supplied.** Flight search now returns matching seeded inventory for matching travel dates, enabling the real Join Waitlist action.
24. **Admin analytics lacked response, queue and failure rates.** Added average queue length, actual confirmation rate, promotion success rate, payment failure rate, average response time, routes and recovered revenue.
25. **Admin invariants were not directly observable.** Added a role-protected invariant endpoint that detects duplicate active seat ownership, occupied seats without active booking ownership, malformed confirmed promotions and duplicate promotion bookings.

## Scenario results

1. Full flight → join — PASS
2. Correct position — PASS
3. Additional join/reorder — PASS
4. Leave/reorder — PASS
5. Confirmed cancellation/refund/seat release — PASS
6. Correct FIFO passenger selected — PASS
7. Fare authorization enforced and skip explained — PASS
8. Transactional HELD seat — PASS
9. Promotion notification — PASS
10. Explicit payment confirmation — PASS
11. Booking/payment/ticket generated — PASS
12. Seat assigned and normalized ownership inserted — PASS
13. Entry becomes CONFIRMED — PASS
14. Next active passenger becomes #1 — PASS
15. Promotion timeout and next passenger — PASS
16. Payment failure and RELEASE_AND_NEXT — PASS
17. Simultaneous processing/confirmation invariants — PASS
18. Multi-seat all-or-nothing — PASS
19. Explicit partial confirmation and remainder entry — PASS
20. Flight cancellation closes queue and releases holds — PASS
21. Schedule/gate changes create revalidation events — PASS
22. SkyBuddy database-grounded status — PASS
23. AI allocation tools absent — PASS
24. Admin analytics and event trail — PASS
25. Responsive mobile rules — PASS

## Security and transaction verification

- Passenger access is session-scoped.
- Cross-user entry, promotion, booking and notification reads are rejected.
- Admin endpoints require AIRLINE_ADMIN/SYSTEM_ADMIN.
- Join, leave, fare authorization, payment, decline and admin actions require explicit confirmation.
- Browser-supplied queue position, price, discount, seat and booking data are ignored.
- FIFO ordering is generated from joined timestamp and stable ID.
- Seat claims use conditional status updates.
- Promotion idempotency keys are unique.
- Payment is unique per booking.
- Confirmed promotion booking ID is unique.
- Invalid fare, seat, payment or offer operations roll back booking, payment, ticket and seat changes.
- AI has no SQL or allocation path.

## Verification commands

```bash
npm test
python3 server/tests/e2e-audit.py
python3 server/tests/offers-e2e.py
python3 server/tests/navigation-e2e.py
python3 server/tests/smart-waitlist-e2e.py
npm run build
```

Results:

- 24/24 unit tests passed
- Core booking/recovery E2E passed
- Offers E2E passed
- Navigation E2E passed
- Smart Waitlist E2E passed
- Server TypeScript validation passed
- Frontend TypeScript/Vite production build passed

## Remaining production constraints

- Payment is simulated; real authorization/capture requires a PCI provider.
- Email/SMS/push adapters are not connected, though delivery status and independent retry semantics exist.
- Probability uses the transparent demo model rather than production cancellation/no-show history.
- The prototype uses controlled visible-page polling; production should use SSE/WebSockets.
- Physical-device mobile testing remains required before commercial release.
- The frontend bundle remains large and should receive route-level lazy loading.
