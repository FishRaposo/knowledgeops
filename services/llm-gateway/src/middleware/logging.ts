/** Structured request logging middleware. */

import { Request, Response, NextFunction } from "express";

interface RequestLog {
  timestamp: string;
  method: string;
  path: string;
  model?: string;
  contentLength?: number;
  userAgent?: string;
}

export function loggingMiddleware(req: Request, res: Response, next: NextFunction): void {
  const startTime = Date.now();

  const logEntry: RequestLog = {
    timestamp: new Date().toISOString(),
    method: req.method,
    path: req.path,
    model: req.body?.model,
    contentLength: req.headers["content-length"]
      ? parseInt(req.headers["content-length"], 10)
      : undefined,
    userAgent: req.headers["user-agent"],
  };

  res.on("finish", () => {
    const duration = Date.now() - startTime;
    const responseLog = {
      ...logEntry,
      statusCode: res.statusCode,
      durationMs: duration,
      cacheStatus: res.getHeader("X-Cache") || "N/A",
    };
    console.log(JSON.stringify(responseLog));
  });

  next();
}
