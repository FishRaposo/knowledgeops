/** LLM Gateway entry point. */

import express from "express";
import { config } from "./config";
import { proxyHandler } from "./proxy/handler";
import { cacheMiddleware } from "./middleware/cache";
import { loggingMiddleware } from "./middleware/logging";
import { budgetMiddleware } from "./middleware/budget";

const app = express();
app.use(express.json({ limit: "10mb" }));

app.use(loggingMiddleware);
app.use(cacheMiddleware);
app.use(budgetMiddleware);

app.post("/v1/chat/completions", proxyHandler.chatCompletion);
app.post("/v1/embeddings", proxyHandler.embedding);
app.get("/v1/models", proxyHandler.listModels);

app.get("/health", (_req, res) => {
  res.json({ status: "healthy", service: "llm-gateway", version: "0.1.0" });
});

app.listen(config.port, () => {
  console.log(`LLM Gateway listening on port ${config.port}`);
  console.log(`Default provider: ${config.defaultProvider}`);
});

export default app;
