# SkyBook Airport Navigation — End-to-End QA Audit

Audit date: 2026-08-18

## Result

The authenticated flight → terminal → gate → current location → graph route → generated directions → synchronized 2D/3D map → arrival workflow passed. Core booking, automatic seat recovery and Offers regressions also passed.

## Defects found and fixed

1. **Polling could reset the passenger to Entrance A every 15 seconds.** The bootstrap callback had stale `current` and `destination` closures. Initialization now uses functional state setters and never overwrites an active manual location/destination unless a verified gate change occurs.
2. **3D user marker was placed on the ground after moving to Floor 2.** Marker height now follows the current node's real graph `y` coordinate.
3. **Floor-2 route lines and nodes were partially inside the 3D floor slab.** Node and route elevations now sit above their corresponding floor geometry.
4. **2D floor coordinate projection placed Floor-1 facilities in the Floor-2 panel and Floor-2 gates off-screen.** Each floor now has an independent normalized projection within its displayed terminal boundary.
5. **FASTEST and SHORTEST returned identical paths.** Seeded escalator travel times now represent moving transport, producing a longer-distance but faster escalator route while SHORTEST retains the shorter stair route.
6. **LOW_WALKING could select stairs.** Weighting now strongly penalizes stairs and favors elevators/escalators/transport.
7. **FAMILY mode did not account for route width.** It now penalizes narrow nodes in addition to preferring elevators and avoiding stairs.
8. **SkyBuddy interpreted “Find a restroom near Gate B24” as flight search.** Flight intent matching was narrowed and facility routing is evaluated before generic gate navigation.
9. **SkyBuddy's old directions were hard-coded.** It now receives route/POI results from `NavigationService` and reports only verified terminal, floor, distance, time and directions.
10. **SkyBuddy Start Navigation could open the page without starting.** Cross-page action state now waits for bootstrap/current location, calculates the route and creates the navigation session.
11. **WebGL detection disabled 3D but did not always switch mode.** A failed WebGL capability check now immediately activates 2D mode.
12. **Offline bootstrap loaded the map but not current location or flight gate.** Cached bootstrap restoration now initializes both; route cache restores matching routes.
13. **2D map exposed zoom controls but no actual pan.** Pointer drag and keyboard arrow-key panning were implemented.
14. **Search autocomplete used visual proximity rather than graph distance.** Search API results now calculate shortest graph distance and walking time from the selected current node.
15. **Selected autocomplete results could reopen stale suggestions.** Search-open state and suggestion clearing were added.
16. **Change Destination left the old route visible.** It now clears route/options/status and focuses a new destination search.
17. **Manual location and destination changes could leave the old navigation active.** They now pause, explain recalculation and request a new graph route from the new state.
18. **Gate change updated the flight but not a structured gate destination.** The operation now maps B24 → A12/T1, emits a route-aware notification, refreshes the gate node and recalculates a shuttle route.
19. **Route-aware journey guidance did not surface delay/status context.** Navigator now displays schedule buffer and route time with an explicit non-guaranteed-advice disclaimer.
20. **Map accessibility metadata was incomplete.** Added map descriptions, `aria-pressed`, labelled zoom/recenter controls, keyboard map focus, text directions and reduced-motion behavior.
21. **New navigation lists produced React key warnings.** Stable keys were added to autocomplete, POIs, route options, directions and admin editor lists.
22. **Demo graph omitted escalator, train and Floor-1 restroom nodes.** They were added with valid edges and searchable POIs.
23. **Admin Airport Map sidebar action was dead.** It now opens the role-protected map editor.
24. **Map editor lacked POI/gate operations.** Added functional POI creation, gate-node mapping, edge editing/deactivation and flight-to-gate mapping APIs/UI actions.
25. **No proactive route-aware notification existed.** Authenticated bootstrap now creates a non-spam navigation notification containing verified graph time/distance for the flight gate.

## GIS/graph integrity checks

- Active nodes: 42+
- All active nodes belong to one connected component
- All active edges have positive distance and walking time
- No accessible edge enters a STAIRS node
- Reported route distance equals the sum of traversed edge distances
- Reported walking time equals the rounded sum of edge time weights
- Floor changes match node-floor transitions
- Terminal changes match T1/T2 transitions
- Shuttle transfer edge is present and labelled seeded demo transport
- Route cache returns a cache hit for repeated common routes
- Admin edits invalidate the cache

## Required QA scenarios

1. Terminal 2 Entrance → Gate B24 — PASS
2. Security → Gate B24 — PASS
3. Gate B24 → Restroom — PASS
4. Gate B24 → Lounge — PASS
5. Gate B24 → Restaurant — PASS
6. Floor 1 → Floor 2 — PASS
7. Terminal 1 → Terminal 2 — PASS
8. Accessible route without stairs — PASS
9. Shortest weighted route — PASS
10. Fastest weighted route — PASS
11. Gate change B24 → A12 — PASS
12. Authenticated flight-aware navigation — PASS
13. SkyBuddy navigation command — PASS
14. Manual destination search/autocomplete — PASS
15. Functional pan/zoom 2D navigation — PASS
16. Structured route-driven 3D navigation — PASS
17. WebGL failure fallback — PASS
18. AI-independent manual fallback — PASS
19. Wrong-direction/location recalculation — PASS
20. Navigation-session arrival detection — PASS
21. Responsive mobile navigation rules — PASS
22. Keyboard/screen-reader/reduced-motion controls — PASS

## Security/API results

- Unauthenticated bootstrap receives no journey: PASS
- Passenger blocked from admin map APIs: PASS
- Invalid start/destination returns 422: PASS
- Invalid route mode returns 400: PASS
- Navigation session ownership enforced: PASS
- Admin node create/move/deactivate: PASS
- Gate mapping requires admin role and confirmation: PASS
- AI has no SQL or route-construction tool: PASS

## Full regression results

- Unit tests: 21/21 passed
- Core booking/waitlist E2E: passed
- Offers E2E: passed
- Navigation E2E: passed
- Server TypeScript validation: passed
- Frontend TypeScript/Vite production build: passed

Commands:

```bash
npm test
python3 server/tests/e2e-audit.py
python3 server/tests/offers-e2e.py
python3 server/tests/navigation-e2e.py
npm run build
```

## Remaining production constraints

- Indoor position is manual/demo; GPS is explicitly not treated as indoor-accurate.
- Airport closures, security queues and transport times are seeded estimates until a real airport operations provider is connected.
- Physical iOS/Android/WebGL testing remains required before commercial deployment.
- Direct SPA paths require host rewrite rules.
- The main bundle remains large and should later receive route-level lazy loading.
