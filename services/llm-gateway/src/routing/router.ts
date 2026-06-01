/** Provider routing based on configuration with instance caching. */

import { LLMProvider } from "../providers/base";
import { OpenAIProvider } from "../providers/openai";
import { MockProvider } from "../providers/mock";

const factories: Record<string, () => LLMProvider> = {
  openai: () => new OpenAIProvider(),
  mock: () => new MockProvider(),
};

const _cache: Record<string, LLMProvider> = {};

export function getProvider(name: string): LLMProvider {
  if (_cache[name]) {
    return _cache[name];
  }
  const factory = factories[name];
  if (!factory) {
    throw new Error(`Unknown provider: ${name}. Available: ${Object.keys(factories).join(", ")}`);
  }
  const instance = factory();
  _cache[name] = instance;
  return instance;
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
  factories[name] = factory;
  delete _cache[name];
}

export function listProviders(): string[] {
  return Object.keys(factories);
}
