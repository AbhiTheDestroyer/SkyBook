import type {AIProvider} from './AIProvider.js';
import type {AssistantContext,AssistantReply} from '../../services/assistant.js';
export class MockAIProvider implements AIProvider{name='MockAIProvider';available=true;async generate(_message:string,_context:AssistantContext,draft:AssistantReply){return{...draft,mode:'DETERMINISTIC' as const}}}
