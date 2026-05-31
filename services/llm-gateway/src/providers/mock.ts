/** Mock LLM provider for testing. */

import { v4 as uuidv4 } from "uuid";
import {
  LLMProvider,
  ChatCompletionRequest,
  ChatCompletionResponse,
  EmbeddingRequest,
  EmbeddingResponse,
} from "./base";

export class MockProvider implements LLMProvider {
  name = "mock";

  async chatCompletion(request: ChatCompletionRequest): Promise<ChatCompletionResponse> {
    const lastMessage = request.messages[request.messages.length - 1];
    return {
      id: `mock-${uuidv4()}`,
      object: "chat.completion",
      created: Math.floor(Date.now() / 1000),
      model: request.model,
      choices: [
        {
          index: 0,
          message: {
            role: "assistant",
            content: `[Mock response for: "${lastMessage?.content?.slice(0, 50)}..."]`,
          },
          finish_reason: "stop",
        },
      ],
      usage: {
        prompt_tokens: lastMessage?.content?.split(" ").length || 0,
        completion_tokens: 20,
        total_tokens: (lastMessage?.content?.split(" ").length || 0) + 20,
      },
    };
  }

  async embedding(request: EmbeddingRequest): Promise<EmbeddingResponse> {
    const inputs = Array.isArray(request.input) ? request.input : [request.input];
    const dimension = 1536;

    return {
      object: "list",
      data: inputs.map((_, index) => ({
        object: "embedding",
        embedding: Array.from({ length: dimension }, () => Math.random() * 2 - 1),
        index,
      })),
      model: request.model,
      usage: {
        prompt_tokens: inputs.reduce((sum, inp) => sum + inp.split(" ").length, 0),
        total_tokens: inputs.reduce((sum, inp) => sum + inp.split(" ").length, 0),
      },
    };
  }
}
