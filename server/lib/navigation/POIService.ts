import type{NavigationService}from'../../services/navigation.js';
export class POIService{constructor(private navigation:NavigationService){}getNearbyPOIs(nodeId:number,categories:string[]=[],limit=10){return this.navigation.nearby(nodeId,categories,limit)}findDestination(query:string){return this.navigation.search(query)}}
