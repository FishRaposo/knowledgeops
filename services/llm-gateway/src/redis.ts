/** Shared Redis client singleton for LLM Gateway.
 *
 *  Both budget.ts and cache.ts create their own Redis instances independently.
 *  This module provides a single shared instance to avoid duplicate connections.
 */

import { Redis } from "ioredis";
import { config } from "./config";

let _redis: Redis | null = null;
let _redisAvailable = false;

export function getRedis(): Redis | null {
  if (_redis) {
    return _redis;
  }
  try {
    _redis = new Redis(config.redisUrl, {
      lazyConnect: true,
      maxRetriesPerRequest: 2,
      retryStrategy: () => null,
    });
    _redis.on("error", () => {
      _redisAvailable = false;
    });
    _redis.on("connect", () => {
      _redisAvailable = true;
    });
  } catch {
    _redisAvailable = false;
  }
  return _redis;
}

export function isRedisAvailable(): boolean {
  return _redisAvailable;
}

export async function tryRedisConnect(): Promise<void> {
  const client = getRedis();
  if (!client) return;
  try {
    await client.connect();
    _redisAvailable = true;
  } catch {
    _redisAvailable = false;
  }
}

// Initialize connection on module load
tryRedisConnect();