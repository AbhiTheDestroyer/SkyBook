export enum ToolPermission{READ_ONLY='READ_ONLY',CONFIRMATION_REQUIRED='CONFIRMATION_REQUIRED',ADMIN_ONLY='ADMIN_ONLY'}
export function canUse(permission:ToolPermission,role:string,confirmed=false){if(permission===ToolPermission.READ_ONLY)return true;if(permission===ToolPermission.ADMIN_ONLY)return['AIRLINE_ADMIN','SYSTEM_ADMIN'].includes(role);return confirmed}
