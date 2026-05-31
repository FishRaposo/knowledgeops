/** Redis-backed budget enforcement middleware. */

import { Request, Response, NextFunction } from "express";
import { Redis } from "ioredis";
import { config } from "../config";

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

const memoryFallback = new Map<string, { spent: number; limit: number; period: string }>();

function getBudgetKey(userId: string): string {
  const month = new Date().toISOString().slice(0, 7);
  return `budget:${userId}:${month}`;
}

function getUserKey(req: Request): string {
  return (req.headers["x-user-id"] as string) || "default";
}

export function budgetMiddleware(req: Request, res: Response, next: NextFunction): void {
  const userId = getUserKey(req);
  const budgetKey = getBudgetKey(userId);

  if (redisAvailable && redis) {
    handleRedisBudget(redis, budgetKey, userId, req, res, next);
  } else {
    handleMemoryBudget(budgetKey, userId, req, res, next);
  }
}

function handleRedisBudget(
  redis: Redis,
  budgetKey: string,
  userId: string,
  req: Request,
  res: Response,
  next: NextFunction,
): void {
  redis
    .get(budgetKey)
    .then((value) => {
      if (value === null) {
        return redis.setex(
          budgetKey,
          2764800,
          JSON.stringify({ spent: 0, limit: config.budgetDefaultMonthly }),
        );
      }
    })
    .then(() => redis.get(budgetKey))
    .then((value) => {
      if (!value) {
        res.status(500).json({ error: { message: "Budget error", type: "budget_error" } });
        return;
      }
      const budgetData: { spent: number; limit: number } = JSON.parse(value);
      if (budgetData.spent >= budgetData.limit) {
        res.status(429).json({
          error: {
            message: `Monthly budget of $${budgetData.limit} exceeded. Current spend: $${budgetData.spent.toFixed(4)}.`,
            type: "budget_exceeded",
          },
        });
        return;
      }

      const originalJson = res.json.bind(res);
      res.json = (body: unknown) => {
        const bodyObj = body as Record<string, unknown>;
        if (bodyObj?.usage) {
          const usage = bodyObj.usage as { prompt_tokens: number; completion_tokens: number };
          const estimatedCost = usage.prompt_tokens * 0.00001 + usage.completion_tokens * 0.00003;
          redis.incrbyfloat(budgetKey, estimatedCost).catch(() => {});
          redis.expire(budgetKey, 2764800).catch(() => {});
        }
        return originalJson(body);
      };

      next();
    })
    .catch(() => {
      next();
    });
}

function handleMemoryBudget(
  budgetKey: string,
  userId: string,
  req: Request,
  res: Response,
  next: NextFunction,
): void {
  if (!memoryFallback.has(budgetKey)) {
    memoryFallback.set(budgetKey, {
      spent: 0,
      limit: config.budgetDefaultMonthly,
      period: new Date().toISOString().slice(0, 7),
    });
  }

  const budget = memoryFallback.get(budgetKey)!;
  if (budget.spent >= budget.limit) {
    res.status(429).json({
      error: {
        message: `Monthly budget of $${budget.limit} exceeded. Current spend: $${budget.spent.toFixed(4)}.`,
        type: "budget_exceeded",
      },
    });
    return;
  }

  const originalJson = res.json.bind(res);
  res.json = (body: unknown) => {
    const bodyObj = body as Record<string, unknown>;
    if (bodyObj?.usage) {
      const usage = bodyObj.usage as { prompt_tokens: number; completion_tokens: number };
      const estimatedCost = usage.prompt_tokens * 0.00001 + usage.completion_tokens * 0.00003;
      budget.spent += estimatedCost;
    }
    return originalJson(body);
  };

  next();
}

export async function getBudgetStatus(userId: string): Promise<{ spent: number; limit: number } | null> {
  const month = new Date().toISOString().slice(0, 7);
  const budgetKey = `budget:${userId}:${month}`;

  if (redisAvailable && redis) {
    try {
      const value = await redis.get(budgetKey);
      if (value) {
        return JSON.parse(value);
      }
    } catch {
      const fallback = memoryFallback.get(budgetKey);
      if (fallback) return { spent: fallback.spent, limit: fallback.limit };
    }
  }

  const fallback = memoryFallback.get(budgetKey);
  if (fallback) return { spent: fallback.spent, limit: fallback.limit };
  return null;
}
