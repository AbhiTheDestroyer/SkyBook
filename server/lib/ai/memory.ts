export type ConversationMemory={origin?:string;destination?:string;date?:string;selectedFlight?:string;selectedBooking?:string;selectedSeat?:string;lastIntent?:string};
export function mergeMemory(previous:ConversationMemory,current:ConversationMemory):ConversationMemory{return{...previous,...Object.fromEntries(Object.entries(current).filter(([,v])=>v!==undefined&&v!==null&&v!==''))}}
