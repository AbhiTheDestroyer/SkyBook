# SkyBook Offers — Full-Stack Audit

Audit date: 2026-08-18

## Outcome

The complete Offers → Flight Search → Discount → Booking → Simulated Payment → Confirmation → Redemption → Cancellation/Refund workflow passed end-to-end. Core non-offer booking and seat-recovery regression tests also passed.

## Defects identified and fixed

1. **Invalid promo errors were reduced to “Request failed” in the UI.** The API client now surfaces backend eligibility reasons.
2. **No durable payment amount existed.** A relational `payments` table now records the backend-calculated final amount, method, transaction ID and status inside the booking transaction.
3. **Offer expiry crossing while a page remained open did not disable Apply.** The Offers page now refreshes its clock every 30 seconds, changes the status to EXPIRED and disables Use Offer without requiring a page reload.
4. **Expiry notification date comparison mixed ISO and SQLite formats.** Comparisons now use `datetime()` normalization.
5. **Admin offer input accepted unsafe values.** Server validation now rejects malformed codes, unsupported types, non-positive values, percentages over 100%, negative fares/caps, invalid dates, invalid limits and unknown routes.
6. **An expired offer could be administratively activated.** Activation now rejects expired records until the expiry date is extended.
7. **Promo-code active state could drift from offer state.** Activate, deactivate and archive operations now synchronize `promo_codes.active`; validation checks it.
8. **Direct status edits could bypass lifecycle endpoints.** Status was removed from generic editing; lifecycle changes use confirmed audited actions.
9. **Offer revenue counted cancelled bookings.** Offer-attributed revenue now includes only CONFIRMED or COMPLETED bookings; redemption history remains immutable.
10. **Rejected promo attempts were not tracked.** `offer_attempts` now records valid/rejected checks and reasons; analytics includes failed attempts and conversion.
11. **Frontend price manipulation required a direct adversarial test.** Sending `total: 1` is ignored; the server recalculates fare, discount, taxes, fees, seat and add-ons.
12. **Invalid promo booking needed rollback verification.** A direct booking with a fake code returns `409`, creates no booking/payment/redemption and leaves the seat AVAILABLE.
13. **Payment correctness lacked an owner-scoped verification API.** `GET /api/bookings/:id/payment` returns only the authenticated owner/admin payment record.
14. **Waitlist-generated bookings lacked payment records.** Recovered bookings now record their authorized demo payment separately; no cancelled-passenger payment is transferred.
15. **Offer filters were incomplete.** Added discount-type and eligibility filters plus highest-discount sorting; route, airline, code and destination remain searchable.
16. **Share links did not open a specific offer.** `/offers/{id}` now opens the matching database offer and updates page metadata.
17. **New Offer UI lists had missing React keys.** Keys were added to avoid console warnings in the new module.
18. **SkyAdmin offer reporting was generic.** It now reports top offer, redemptions, total discount, confirmed offer revenue and conversion from database aggregates.

## Security controls verified

- Offer eligibility, discount and total are calculated server-side.
- Authenticated identity comes from hashed expiring sessions, not request email.
- Admin endpoints require AIRLINE_ADMIN or SYSTEM_ADMIN.
- Apply is explicit; AI never silently applies a code.
- Booking revalidates the promo inside the same transaction as seat allocation and redemption.
- One code per booking.
- Per-user and global limits are checked transactionally.
- Unique `(offer_id, booking_id)` prevents duplicate redemption.
- Concurrent final-coupon test gives one success and one safe `409`.
- Invalid/expired/ineligible promo leaves the seat unchanged.
- SQL mutations use prepared parameters; dynamic update columns come only from an internal allowlist.
- Historical redemption rows survive cancellation and refund.
- Admin mutations are written to `offer_audit_logs`.
- Saved offers and payments are owner-scoped.

## Scenario results

1. New user welcome offer — PASS
2. Verified demo student offer — PASS
3. Normal user denied student offer — PASS
4. Expired offer denied — PASS
5. Route restriction — PASS
6. Airline restriction — PASS
7. Minimum fare — PASS
8. Maximum discount exact cap — PASS
9. Per-user limit — PASS
10. Global limit — PASS
11. Concurrent final-use race — PASS
12. Promo revalidated during booking — PASS
13. Backend recalculation defeats `total: 1` — PASS
14. Checkout breakdown source verified — PASS
15. Payment record equals final backend total — PASS
16. Booking/redemption record — PASS
17. Discounted refund calculation — PASS
18. SkyBuddy database offer recommendation — PASS
19. Admin create/edit/activate/deactivate/archive — PASS
20. Admin redemption analytics — PASS
21. Responsive mobile rules — PASS
22. Timestamp-based countdown and live expiry — PASS
23. Saved offers — PASS
24. Offer notifications — PASS
25. Core booking/waitlist recovery regressions — PASS

## Test commands

```bash
npm test
python3 server/tests/e2e-audit.py
python3 server/tests/offers-e2e.py
npm run build
```

Results:

- 21/21 unit tests passed
- All core E2E audit checks passed
- All Offers E2E checks passed
- Server TypeScript validation passed
- Frontend TypeScript and production Vite build passed

## Remaining deployment limitations

- Payment remains deliberately simulated; the persisted payment record proves amount integrity but is not a PCI processor transaction.
- Real airline inventory and real-model behavior depend on configured Amadeus/AI credentials.
- Responsive behavior is covered by CSS/source assertions and production compilation; physical iOS/Android GPU/browser testing remains required before commercial release.
- Direct `/offers/{id}` URLs require the production web server/CDN to rewrite SPA routes to `index.html`.
- The frontend bundle remains large and should receive route-level lazy loading in a later performance pass.
