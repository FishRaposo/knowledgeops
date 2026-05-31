/** Request handler for OpenAI-compatible proxy endpoints. */

import { Request, Response } from "express";
import { getProviderForModel } from "../routing/router";
import { config } from "../config";

export interface ChatCompletionRequest {
  model: string;
  messages: Array<{ role: string; content: string }>;
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
}

export interface EmbeddingRequest {
  model: string;
  input: string | string[];
}

export interface ModelInfo {
  id: string;
  object: string;
  owned_by: string;
}

export const proxyHandler = {
  async chatCompletion(req: Request, res: Response): Promise<void> {
    const body = req.body as ChatCompletionRequest;
    const model = body.model || config.defaultModel;
    const provider = getProviderForModel(model, config.modelProviderMap, config.defaultProvider);

    try {
      const result = await provider.chatCompletion({ ...body, model });
      res.json(result);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Unknown error";
      res.status(500).json({ error: { message, type: "provider_error" } });
    }
  },

  async embedding(req: Request, res: Response): Promise<void> {
    const body = req.body as EmbeddingRequest;
    const model = body.model || config.embeddingModel;
    const provider = getProviderForModel(model, config.embeddingProviderMap, config.defaultProvider);

    try {
      const result = await provider.embedding({ ...body, model });
      res.json(result);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Unknown error";
      res.status(500).json({ error: { message, type: "provider_error" } });
    }
  },

  async listModels(_req: Request, res: Response): Promise<void> {
    const models: ModelInfo[] = [
      { id: "gpt-4o", object: "model", owned_by: "openai" },
      { id: "gpt-4o-mini", object: "model", owned_by: "openai" },
      { id: "text-embedding-3-small", object: "model", owned_by: "openai" },
    ];
    res.json({ object: "list", data: models });
  },
};
