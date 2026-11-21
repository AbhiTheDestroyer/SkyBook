import type{SmartWaitlistService}from'../../services/waitlist.js';export class WaitlistAnalyticsService{constructor(private service:SmartWaitlistService){}get(){return this.service.analytics()}}
