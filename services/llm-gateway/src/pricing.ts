/** Model pricing and cost estimation helpers for LLM Gateway. */

export interface ModelPricing {
  prompt: number;
  completion: number;
}

export const MODEL_PRICING: Record<string, ModelPricing> = {
  "gpt-4o": { prompt: 0.000005, completion: 0.000015 },
  "gpt-4o-mini": { prompt: 0.00000015, completion: 0.0000006 },
  "text-embedding-3-small": { prompt: 0.00000002, completion: 0.0 },
  "gpt-4-turbo": { prompt: 0.00001, completion: 0.00003 },
  "gpt-3.5-turbo": { prompt: 0.0000005, completion: 0.0000015 },
};

export function estimateCost(model: string, promptTokens: number, completionTokens: number): number {
  const pricing = MODEL_PRICING[model] || { prompt: 0.00001, completion: 0.00003 };
  return promptTokens * pricing.prompt + completionTokens * pricing.completion;
}
