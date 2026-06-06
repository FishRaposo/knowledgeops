/** Redis-backed response cache middleware with in-memory fallback. */

import { Request, Response, NextFunction } from "express";
import crypto from "crypto";
import { config } from "../config";
import { getRedis, isRedisAvailable } from "../redis";

interface CacheEntry {
  body: unknown;
  timestamp: number;
}

const memoryFallback = new Map<string, CacheEntry>();

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
  const redis = getRedis();

  if (isRedisAvailable() && redis) {
    redis.get(key).then((cached) => {
      if (cached) {
        try {
          const entry: CacheEntry = JSON.parse(cached);
          res.setHeader("X-Cache", "HIT");
          res.json(entry.body);
        } catch {
          missAndStoreRedis(key, redis, req, res, next);
        }
      } else {
        missAndStoreRedis(key, redis, req, res, next);
      }
    }).catch(() => {
      fallbackMissAndStore(key, req, res, next);
    });
    return;
  }

  fallbackMissAndStore(key, req, res, next);
}

function missAndStoreRedis(key: string, redis: any, req: Request, res: Response, next: NextFunction): void {
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
