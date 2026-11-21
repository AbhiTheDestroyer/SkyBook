import type {AssistantContext,AssistantReply} from '../../services/assistant.js';
export interface AIProvider{name:string;available:boolean;generate(message:string,context:AssistantContext,draft:AssistantReply):Promise<AssistantReply>}
