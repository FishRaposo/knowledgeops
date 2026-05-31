/** Provider routing based on configuration. */

import { LLMProvider } from "../providers/base";
import { OpenAIProvider } from "../providers/openai";
import { MockProvider } from "../providers/mock";

const providers: Record<string, () => LLMProvider> = {
  openai: () => new OpenAIProvider(),
  mock: () => new MockProvider(),
};

export function getProvider(name: string): LLMProvider {
  const factory = providers[name];
  if (!factory) {
    throw new Error(`Unknown provider: ${name}. Available: ${Object.keys(providers).join(", ")}`);
  }
  return factory();
}

export function getProviderForModel(
  model: string,
  modelProviderMap: Record<string, string>,
  defaultProviderName: string,
): LLMProvider {
  const providerName = modelProviderMap[model] || defaultProviderName;
  return getProvider(providerName);
}

export function registerProvider(name: string, factory: () => LLMProvider): void {
  providers[name] = factory;
}

export function listProviders(): string[] {
  return Object.keys(providers);
}
