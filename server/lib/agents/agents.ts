export type AgentDefinition={name:string;intents:string[];tools:string[];description:string};
export const AGENTS:AgentDefinition[]=[
{name:'FlightSearchAgent',intents:['FLIGHT_SEARCH','FLIGHT_SEARCH_EMPTY','FLIGHT_SEARCH_NEEDS_ROUTE'],tools:['searchFlights','compareFlights'],description:'Searches verified flight inventory and applies user filters.'},
{name:'FlightRecommendationAgent',intents:['RECOMMENDATION'],tools:['searchFlights','compareFlights'],description:'Scores verified offers and explains preference-based recommendations.'},
{name:'BookingAssistantAgent',intents:['DOCUMENTS','BOOKING','BOOKING_CHANGE'],tools:['getBooking','getBookingHistory','modifyBooking'],description:'Retrieves only the authenticated passenger booking context.'},
{name:'SeatAssistantAgent',intents:['SEAT'],tools:['getSeatMap','recommendSeat','reserveSeat'],description:'Recommends available seats; reservation requires confirmation.'},
{name:'WaitlistAgent',intents:['WAITLIST','WAITLIST_NONE'],tools:['getWaitlistStatus','predictWaitlistProbability'],description:'Explains transparent FIFO status and demo probability.'},
{name:'RefundAgent',intents:['REFUND','CANCELLATION','CANCELLATION_NO_BOOKING'],tools:['calculateRefund','cancelBooking','requestRefund'],description:'Calculates estimates and gates cancellation behind confirmation.'},
{name:'FlightMonitoringAgent',intents:['FLIGHT_STATUS'],tools:['getFlightStatus'],description:'Reports verified operational flight data.'},
{name:'TripPlanningAgent',intents:['TRIP_PLAN'],tools:['generateTravelPlan'],description:'Creates structured destination plans from static demo knowledge.'},
{name:'AirportNavigationAgent',intents:['NAVIGATION','FACILITY'],tools:['getAirportMap','calculateRoute'],description:'Connects chat actions to indoor 2D and 3D wayfinding.'},
{name:'BaggageAssistantAgent',intents:['BAGGAGE','ADD_ONS'],tools:['getBaggageAllowance','purchaseAddon'],description:'Uses fare baggage data and confirms purchases.'},
{name:'CustomerSupportAgent',intents:['SUPPORT','SAFE_FALLBACK'],tools:['createSupportTicket'],description:'Answers supported topics or offers a support ticket.'},
{name:'PersonalizationAgent',intents:['PREFERENCES'],tools:['getUserPreferences','updateUserPreferences'],description:'Manages non-sensitive editable travel preferences.'},
{name:'OfferRecommendationAgent',intents:['OFFERS','OFFER_RECOMMENDATION'],tools:['searchOffers','validatePromoCode','getBestOffer','applyOffer'],description:'Retrieves database offers and calculates eligibility and savings without auto-applying.'},
{name:'JourneyAgent',intents:['JOURNEY','JOURNEY_NONE'],tools:['getBooking','getFlightStatus','getBaggageAllowance','getAirportMap'],description:'Builds answers from the authenticated journey aggregate and next-action engine.'},
{name:'NotificationAgent',intents:['NOTIFICATIONS'],tools:['getFlightStatus'],description:'Explains proactive journey changes.'},
{name:'SkyAdminAgent',intents:['ADMIN_ANALYTICS'],tools:['manageFlights'],description:'Produces authorized database-backed operational insights.'}
];
export function selectAgent(intent:string){return AGENTS.find(a=>a.intents.includes(intent))||AGENTS.find(a=>a.name==='CustomerSupportAgent')!}
