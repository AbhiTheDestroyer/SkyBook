# SKYBOOK

**BOOK. RECOVER. NAVIGATE.**

A functional full-stack travel-tech demonstration built with React, TypeScript, React Three Fiber, Express, and relational SQLite.

## Run

```bash
npm install
npm run dev
```

- Web app: `http://localhost:5173`
- API: `http://localhost:3001/api`

## Best demo path

1. On the landing page, use the seeded **DEL → BOM** search.
2. Select SK102 or SK218 and complete fare, passenger, cabin seat, baggage, and simulated payment steps.
3. Open **My Journey** to see the live journey timeline and notifications.
4. Open **Smart Waitlist**, click **Cancel Passenger X & recover seat**.
5. Observe the atomic workflow: Passenger X cancelled → ₹4,500 refund initiated → 14A released → Rahul matched by FIFO and maximum-fare eligibility → new booking/PNR/ticket → notification.
6. Open **Airport Navigation**, switch to **3D**, and start the guided virtual tour from Entrance A → Check-in → Security → Concourse → Gate 24. You can pause, orbit, zoom, reset, and select terminal POIs.
7. On the landing page, scroll to the **3D Earth Route Explorer**. Drag/zoom the globe, select an airport beacon, inspect animated great-circle routes, and launch a route search.
8. Open the profile/operations control to enter the admin dashboard, delay SK102, change its gate, or reset all demo data.

## Enable global live airport and flight data (Amadeus)

SkyBook now includes a server-side Amadeus Self-Service adapter. Airport autocomplete and flight-offer search use global Amadeus coverage when credentials are configured. API secrets are never sent to the browser.

1. Create an application at [Amadeus for Developers](https://developers.amadeus.com/).
2. Copy the environment template:

```bash
cp .env.example .env
```

3. Add your sandbox credentials to `.env`:

```env
AMADEUS_API_KEY=your_api_key
AMADEUS_API_SECRET=your_api_secret
AMADEUS_BASE_URL=https://test.api.amadeus.com
```

4. Restart `npm run dev`.
5. Verify the active provider:

```bash
curl http://localhost:3001/api/health
```

The response will show `"aviationProvider":"AMADEUS"`. Without credentials—or if the upstream sandbox is unavailable—SkyBook deliberately switches to the labeled `DEMO_DYNAMIC` generator. The fallback contains 60+ Indian airports, major international hubs, deterministic schedules, INR fares, baggage, duration, stop count, seat inventory, and bookable database records.

> No single API returns literally every aircraft movement or a guaranteed fare for every airport. Results are limited to routes and offers available in the connected Amadeus environment. Production access and airline content agreements are required for commercial use.

## My Journey travel command center

My Journey is now a database-backed aggregate over authenticated bookings, flights, passengers, normalized seats, payments, tickets, refunds, baggage, waitlists, airport navigation, offers and notifications.

It provides upcoming/ongoing/completed/cancelled/waitlisted filters, search, dynamic journey cards, a controlled state machine, status-driven timeline, check-in eligibility and completion, boarding pass/ticket access, seat changes through existing inventory, baggage purchases, payment/refund breakdowns, airport navigation, personal tasks, privacy-safe document status, journey sharing, offers, cancellation and SkyBuddy context.

Journey state is synchronized from booking/check-in/flight status using controlled 15-second visible-page polling. Gate, terminal, delay, boarding, departure, arrival and cancellation changes create journey events and alerts. Non-sensitive data is cached for an explicitly labelled offline fallback.

Role-protected admin analytics aggregate active/delayed/cancelled/completed journeys, check-in rate, navigation launches, waitlist conversions and offer conversions without exposing document/payment credentials.

Test:

```bash
python3 server/tests/journey-e2e.py  # requires npm run dev
```

## Smart Waitlist

SkyBook now includes a second-generation deterministic Smart Waitlist alongside the legacy recovery demonstration.

### Core workflow

```text
Sold-out flight → authenticated join → eligibility → FIFO position
→ maximum fare authorization → explainable probability
→ cancellation/seat release → atomic seat hold → 15-minute promotion
→ explicit demo payment → booking/payment/ticket → queue update → notification
```

Actual seat allocation is performed only by `SmartWaitlistService` and the deterministic matching engine. SkyBuddy can explain status, probability and alternatives but cannot change queue order, hold seats, confirm payment or create bookings.

The relational model includes `waitlist_entries`, `waitlist_promotions`, `waitlist_events` and `waitlist_config`. Seats use an explicit `HELD` state during the promotion window. Idempotency keys, conditional seat updates, transactions and confirmed-seat uniqueness prevent duplicate allocation.

The passenger dashboard supports join, leave, fare-limit updates, anonymous queue visualization, probability factors, event history, promotion countdown, offer selection, payment success/failure, decline/expiry, partial group confirmation, 3D seat preview, ticket access and airport navigation. Controlled 15-second polling runs only while visible.

The admin dashboard reports queue/promotion/payment analytics and provides controlled retry/matching operations; no admin action directly edits seat ownership or queue positions.

Exact five-seat demo:

```text
POST /api/demo/waitlist/reset
Passenger A cancels → 11A HELD for Passenger F
Passenger F confirms → booking/payment/ticket created
Passenger G moves to #1
```

Test:

```bash
python3 server/tests/smart-waitlist-e2e.py  # requires npm run dev
```

## Airport Navigator

SkyBook now includes a graph-driven indoor navigation system for **SkyBook International Airport — Seeded Demo Data**.

### Data and route engine

The relational model includes navigation terminals, floors, nodes, edges, POIs, gates, terminal transfers, navigation sessions and audit logs. More than 40 connected nodes cover Terminal 1 and Terminal 2, two floors, Entrance A, check-in, security, immigration, customs, baggage claim, elevators, escalators, stairs, gates A12 and B20–B25, lounge, restaurant, café, two restrooms, ATM, medical, help, parking, taxi, bus, metro and regional train.

`NavigationService` uses Dijkstra-based pathfinding. It generates FASTEST, SHORTEST, ACCESSIBLE, LOW_WALKING and FAMILY routes; accessible paths reject stairs. Results contain graph nodes, traversed edges, distance, configured walking/processing time, floor changes, terminal transfers and generated turn-by-turn instructions. Common routes are cached and cache is invalidated after map edits.

### Passenger experience

Open **Airport Navigation** or `/airport-navigation` to:

- Search gates, facilities and graph nodes with autocomplete and graph distance.
- Manually set current indoor location; browser location is clearly labelled outdoor-only.
- Use flight-aware Navigate to Gate for the authenticated booking.
- Switch synchronized 2D/3D modes without losing route state.
- Pan, zoom and recenter the 2D graph.
- Orbit and zoom the structured 3D digital twin.
- Select route mode, view text directions and advance with **I'm here**.
- Recalculate after destination/location/gate changes.
- Complete a navigation session and display **You Arrived**.
- Load saved map/route data when the navigation API is temporarily unavailable.

### SkyBuddy and operations

SkyBuddy navigation answers are grounded in `NavigationService` and `POIService` results; it will not invent a gate, facility, route, distance or walking time. Navigation action cards open the correct 3D destination and start the route.

Gate changes update the flight-to-gate node mapping, generate notifications, refresh the passenger destination and trigger route recalculation. Route-aware notifications show verified graph distance/time. Delay status is surfaced with schedule-aware, non-guaranteed travel guidance.

Administrators can open **Operations → Map editor** to create/move/deactivate nodes, connect nodes, set accessibility, add POIs/gates and map a flight to a gate. Admin APIs are role-protected and map changes invalidate route cache and create audit records.

Test:

```bash
python3 server/tests/navigation-e2e.py  # requires npm run dev
```

## Offers & Deals module

SkyBook now has a relational, end-to-end promotion marketplace rather than static marketing cards.

### Passenger flow

- Browse/search/filter/sort database offers on **Offers**.
- Open details, inspect status, dates, routes, airlines, cabins, eligibility, usage remaining and terms.
- Save/remove offers and receive an in-app saved-offer notification.
- Copy or share `/offers/{id}` links.
- Use an offer to prefill route search.
- Review the backend-calculated best eligible offer on each flight.
- Explicitly select **Apply offer**; one offer is allowed per booking.
- Apply/remove a promo at checkout and see base fare, discount, taxes, fees, seat/add-ons, final total and savings.
- The backend revalidates and recalculates immediately before the simulated payment/booking transaction.
- Successful redemption, savings notification, cancellation and discounted refund history are persisted.

### Offer rules

The centralized `OfferService`, `OfferEligibilityService` behavior and `DiscountEngine` enforce status, booking/travel dates, minimum/maximum fare, route, domestic/international category, airline, cabin, weekend travel date, new-user history, demo student status, family size, global usage limit and per-user limit. Percentage, fixed and capped discounts cannot reduce fare below zero.

### Administration

From Operations choose **Manage offers**. Admins can create a draft or publish, edit safe fields, duplicate, activate/deactivate, archive and inspect database-backed analytics. Historical discount/code fields become immutable after redemption. Every admin mutation creates an offer audit record. SkyAdmin can report offer totals and prepare a disabled route-offer draft, but confirmation is required before creation and publishing remains separate.

### Offer APIs

- `GET /api/offers`, `GET /api/offers/:id`
- `POST /api/offers/validate`, `/apply`, `/remove`, `/save`
- `GET /api/offers/best`, `/personalized`, `/saved/list`
- `DELETE /api/offers/save/:id`
- Admin create/update/duplicate/activate/deactivate/archive and analytics endpoints under `/api/admin/offers`

Demo promotions are visibly labelled **DEMO OFFER** and include SKYWELCOME500, STUDENT500, SAVE15, WEEKEND10, BUSINESS10, JAI-MUM and INTERNATIONAL15.

Tests:

```bash
npm test
python3 server/tests/offers-e2e.py  # with npm run dev running
```

## SkyBuddy AI multi-agent system

SkyBook now includes **Skye**, an animated aviation companion/avatar. Skye floats on every passenger and administrator screen, reacts while listening/thinking/completing work, accepts speech or typed commands, and reads results aloud when voice output is enabled.

SkyBuddy is routed through a central `AIOrchestrator` and specialist agents:

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

The orchestrator selects a specialist and its allowlisted tools, receives verified context from the service/database layer, and then uses either `MockAIProvider` or `RealAIProvider`. The model never receives direct SQL access. The tool registry classifies tools as `READ_ONLY`, `CONFIRMATION_REQUIRED`, or `ADMIN_ONLY`.

Conversation messages and non-sensitive short-term memory are associated with a conversation ID. SkyBuddy can therefore understand follow-ups such as:

1. “Find a cheap flight from Delhi to Mumbai.”
2. “Which one do you recommend?”
3. “Find me a window seat.”

Users can start a new conversation, which clears the stored conversation thread. Preferences and proactive-notification settings have dedicated database records and can only be updated with confirmation. Support-ticket creation also requires confirmation.

## SkyBook Automation Agent

A global floating automation agent is available on passenger and admin screens. It accepts typed commands and browser speech recognition, creates an auditable action plan, and executes approved SkyBook tools.

Example commands:

- “Find the cheapest direct flight from Jaipur to Dubai tomorrow.”
- “Open my boarding pass.”
- “Open my journey and navigate to the gate.”
- “Delay flight SK102.”
- “Change the gate for SK102.”
- “Cancel Passenger X and recover the seat.”
- “Reset the demonstration.”

Low-risk navigation and search steps run automatically. Booking cancellation, refund/recovery operations, flight delays, gate changes, booking review, and demo reset are classified as medium/high risk and always stop at a confirmation card. The agent displays every tool step before execution and writes plan/execution metadata to the audit log.

### Voice commands

Click the floating sparkle button, then the microphone. Chrome/Edge use the Web Speech API to transcribe the command. Final speech is automatically submitted to the planner. Spoken responses use the browser Speech Synthesis API and can be muted with the speaker toggle.

Microphone access requires browser permission and a secure origin (`https` or `localhost`). Text commands remain available when speech recognition is unsupported.

### Agent architecture

```text
Voice / text command
       ↓
Speech-to-text (browser, when enabled)
       ↓
POST /api/agent/plan
       ↓
Allowlisted deterministic planner
       ↓
Risk classification and confirmation gate
       ↓
Navigation / search / approved API tools
       ↓
Execution result + audit log + optional speech response
```

The agent does not silently complete simulated payment, choose passenger identity, cancel bookings, alter operations, or reset data. Those actions require passenger/admin review. Camera and visual input are labelled as requiring a configured multimodal provider; SkyBook does not pretend to interpret unsupported visual content.

## Sky Assist

Sky Assist now runs through `POST /api/assistant` and is connected to current bookings, flight inventory, waitlist entries, notifications, airport data, fares, baggage and route information.

It supports natural queries such as:

- “Find the cheapest direct flight from Jaipur to Dubai on 2026-08-25 under 30000.”
- “Can I carry 20 kg baggage?”
- “What cancellation refund will I receive?”
- “What are my waitlist chances?”
- “How do I reach my boarding gate?”
- “Show my flight status and boarding pass.”

Without an AI key, an explainable deterministic intent engine answers supported SkyBook topics and labels itself **SAFE DEMO ENGINE**. To enable broader natural-language responses, configure an OpenAI-compatible provider in `.env`:

```env
AI_API_KEY=your_key
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini
```

The API key stays server-side. Live-model prompts are grounded with current SkyBook data, use low temperature, prohibit invented fares/statuses/gates/refunds, and fall back to the deterministic engine on provider errors. Assistant intent, mode and confidence are written to the audit log; message text and credentials are not written there.

## Aviation provider design

- `GET /api/airports?q=...` searches the relational airport catalog and merges live Amadeus airport results.
- `GET /api/flights?from=DEL&to=DXB&date=2026-08-25&adults=1&cabin=ECONOMY` returns live flight offers or deterministic fallback inventory.
- Live offers are normalized into SkyBook's internal flight model and materialized with seat inventory so the existing booking workflow remains functional.
- Provider failures degrade safely without exposing credentials or breaking search.
- Airport records are indexed by IATA, city, and country.

## Architecture

```text
React UI / isolated 3D components
        ↓
REST API (Express)
        ↓
Service/workflow functions
        ↓
Prepared-query data access
        ↓
SQLite relational database (FKs, unique constraints, WAL)
```

The Vite proxy keeps browser calls relative (`/api`), making the frontend independent of the backend host. External airline, payment, AI, and map calls are represented by explicit deterministic demo implementations; the UI never claims that they are live AI or real payment services.

## Core algorithms

### Atomic seat recovery

`cancelAndRecover()` runs as one database transaction:

1. Lock the workflow around a confirmed booking.
2. Calculate cancellation fee and refund.
3. Mark booking cancelled/payment refunded.
4. Release the assigned seat.
5. Find the first waiting entry for the same flight whose seat count and maximum authorization are compatible with the current fare.
6. Occupy the released seat, create a new booking and ticket, confirm the waitlist entry, create a notification, and write an audit log.
7. Commit all changes together; any thrown error rolls back everything.

A unique `(flight_id, seat_label)` database constraint plus a guarded available-seat update prevents duplicate inventory records.

### Recommendation

Seeded results are ranked with an explainable weighted balance of price, duration, stops, departure time, and availability. The interface labels this as **algorithmic**, not a live AI model.

### Waitlist probability

The demo score decreases by queue position and is presented as **DEMO PROBABILITY**. It is advisory and never controls allocation.

### Indoor route

The terminal model uses graph-style nodes (Entrance, Check-in, Security, Concourse, Gate) and a deterministic route. The rendered 2D/3D modes are independent from the journey and flight data, so an A*/Dijkstra provider can replace the seeded route engine.

## Security and data safety

- Passwords use salted `scrypt`; hashes are never returned.
- Authentication endpoints compare hashes with a timing-safe comparison.
- SQL mutations use prepared statements.
- Payment is explicitly simulated; no real card credentials are accepted or stored.
- Server-side validation and safe HTTP errors are used for key workflows.
- Audit logs capture seat recovery.
- SQLite foreign keys and WAL mode are enabled.

Seeded admin API account: `admin@skybook.demo` / `Admin@123` (demonstration only).

## Accessibility and performance

- Semantic buttons/forms, visible focus states, high contrast, labels, and text alternatives.
- 3D is enhancement-only; all travel actions have 2D controls.
- `prefers-reduced-motion` disables nonessential motion and the 3D hero.
- Responsive cabin, terminal, booking, passenger, and operations interfaces.
- React Three Fiber canvas uses bounded DPR and a low-poly procedural aircraft.

## Important files

- `src/main.tsx` — product UI and separated visual components
- `src/styles.css` — responsive premium aviation design system
- `server/index.ts` — schema, seed data, APIs, booking and recovery transactions
- `data/skybook.db` — generated relational demo database
- `vite.config.ts` — web/API development proxy
