import{AIOrchestrator}from'./AIOrchestrator.js';import{MockAIProvider}from'./MockAIProvider.js';import{RealAIProvider}from'./RealAIProvider.js';
export function createAIService(){const real=new RealAIProvider();return new AIOrchestrator(real.available?real:new MockAIProvider())}
