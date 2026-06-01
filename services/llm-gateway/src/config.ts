/** LLM Gateway configuration. */

export interface GatewayConfig {
  port: number;
  openaiApiKey: string;
  defaultProvider: string;
  defaultModel: string;
  embeddingModel: string;
  redisUrl: string;
  cacheTtlSeconds: number;
  budgetDefaultMonthly: number;
  logLevel: string;
  modelProviderMap: Record<string, string>;
  embeddingProviderMap: Record<string, string>;
}

const defaultModelProviderMap: Record<string, string> = {
  "gpt-4o": "openai",
  "gpt-4o-mini": "openai",
  "gpt-4-turbo": "openai",
  "gpt-3.5-turbo": "openai",
};

const defaultEmbeddingProviderMap: Record<string, string> = {
  "text-embedding-3-small": "openai",
  "text-embedding-3-large": "openai",
  "text-embedding-ada-002": "openai",
};

const _openaiKey = process.env.OPENAI_API_KEY || "";
const _defaultProvider = _openaiKey
  ? (process.env.DEFAULT_PROVIDER || "openai")
  : "mock";

export const config: GatewayConfig = {
  port: parseInt(process.env.PORT || "8004", 10),
  openaiApiKey: _openaiKey,
  defaultProvider: _defaultProvider,
  defaultModel: process.env.DEFAULT_MODEL || "gpt-4o-mini",
  embeddingModel: process.env.EMBEDDING_MODEL || "text-embedding-3-small",
  redisUrl: process.env.REDIS_URL || "redis://redis:6379/0",
  cacheTtlSeconds: parseInt(process.env.CACHE_TTL_SECONDS || "3600", 10),
  budgetDefaultMonthly: parseFloat(process.env.BUDGET_DEFAULT_MONTHLY || "100.00"),
  logLevel: process.env.LOG_LEVEL || "INFO",
  modelProviderMap: defaultModelProviderMap,
  embeddingProviderMap: defaultEmbeddingProviderMap,
};
