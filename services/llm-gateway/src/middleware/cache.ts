/** Redis-backed response cache middleware with in-memory fallback. */

import { Request, Response, NextFunction } from "express";
import { Redis } from "ioredis";
import crypto from "crypto";
import { config } from "../config";

interface CacheEntry {
  body: unknown;
  timestamp: number;
}

const memoryFallback = new Map<string, CacheEntry>();

let redis: Redis | null = null;
let redisAvailable = false;

function getRedis(): Redis | null {
  if (redis) {
    return redis;
  }
  try {
    redis = new Redis(config.redisUrl, {
      lazyConnect: true,
      maxRetriesPerRequest: 2,
      retryStrategy: () => null,
    });
    redis.on("error", () => {
      redisAvailable = false;
    });
    redis.on("connect", () => {
      redisAvailable = true;
    });
  } catch {
    redisAvailable = false;
  }
  return redis;
}

async function tryRedisConnect(): Promise<void> {
  const client = getRedis();
  if (!client) return;
  try {
    await client.connect();
    redisAvailable = true;
  } catch {
    redisAvailable = false;
  }
}

tryRedisConnect();

function getCacheKey(req: Request): string {
  const payload = JSON.stringify({ path: req.path, body: req.body });
  return crypto.createHash("sha256").update(payload).digest("hex");
}

export function cacheMiddleware(req: Request, res: Response, next: NextFunction): void {
  if (req.method !== "POST" || !config.cacheTtlSeconds) {
    next();
    return;
  }

  const key = getCacheKey(req);

  if (redisAvailable && redis) {
    redis.get(key).then((cached) => {
      if (cached) {
        try {
          const entry: CacheEntry = JSON.parse(cached);
          res.setHeader("X-Cache", "HIT");
          res.json(entry.body);
        } catch {
          missAndStoreRedis(key, req, res, next);
        }
      } else {
        missAndStoreRedis(key, req, res, next);
      }
    }).catch(() => {
      fallbackMissAndStore(key, req, res, next);
    });
    return;
  }

  fallbackMissAndStore(key, req, res, next);
}

function missAndStoreRedis(key: string, req: Request, res: Response, next: NextFunction): void {
  const originalJson = res.json.bind(res);
  res.json = (body: unknown) => {
    if (redis) {
      const entry: CacheEntry = { body, timestamp: Date.now() };
      redis.setex(key, config.cacheTtlSeconds, JSON.stringify(entry)).catch(() => {});
    }
    res.setHeader("X-Cache", "MISS");
    return originalJson(body);
  };
  next();
}

function fallbackMissAndStore(key: string, _req: Request, res: Response, next: NextFunction): void {
  const cached = memoryFallback.get(key);
  if (cached && Date.now() - cached.timestamp < config.cacheTtlSeconds * 1000) {
    res.setHeader("X-Cache", "HIT");
    res.json(cached.body);
    return;
  }

  const originalJson = res.json.bind(res);
  res.json = (body: unknown) => {
    memoryFallback.set(key, { body, timestamp: Date.now() });
    res.setHeader("X-Cache", "MISS");
    return originalJson(body);
  };
  next();
}
