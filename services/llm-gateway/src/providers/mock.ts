/** Mock LLM provider for offline-first demo and testing.

Produces deterministic embeddings and chat completions so that
repeatable queries always yield the same vectors and answers.
*/

import { v4 as uuidv4 } from "uuid";
import {
  LLMProvider,
  ChatCompletionRequest,
  ChatCompletionResponse,
  ChatCompletionChunk,
  EmbeddingRequest,
  EmbeddingResponse,
} from "./base";

const DIMENSION = 1536;

/** Simple string hash for seeding deterministic values. */
function _hashString(input: string): number {
  let h = 2166136261;
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

/** Seeded pseudo-random generator (Mulberry32). */
function _mulberry32(seed: number): () => number {
  return () => {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Generate a deterministic embedding vector for a text input. */
function _deterministicEmbedding(text: string): number[] {
  const seed = _hashString(text);
  const rng = _mulberry32(seed);
  return Array.from({ length: DIMENSION }, () => rng() * 2 - 1);
}

export class MockProvider implements LLMProvider {
  name = "mock";

  async chatCompletion(request: ChatCompletionRequest): Promise<ChatCompletionResponse> {
    const lastMessage = request.messages[request.messages.length - 1];
    const query = lastMessage?.content?.trim() || "";
    const hash = _hashString(query);

    // Deterministic answer templates based on query hash
    const templates = [
      "According to the available documentation, this refers to ",
      "Based on the knowledge base, the answer is related to ",
      "The documents indicate that this concerns ",
    ];
    const template = templates[hash % templates.length];
    const answer = `${template}"${query.slice(0, 60)}". Please consult the cited sources for full details.`;

    return {
      id: `mock-${hash.toString(16)}`,
      object: "chat.completion",
      created: Math.floor(Date.now() / 1000),
      model: request.model,
      choices: [
        {
          index: 0,
          message: {
            role: "assistant",
            content: answer,
          },
          finish_reason: "stop",
        },
      ],
      usage: {
        prompt_tokens: query.split(/\s+/).length || 0,
        completion_tokens: answer.split(/\s+/).length || 0,
        total_tokens:
          (query.split(/\s+/).length || 0) + (answer.split(/\s+/).length || 0),
      },
    };
  }

  async *streamChatCompletion(request: ChatCompletionRequest): AsyncGenerator<ChatCompletionChunk> {
    const lastMessage = request.messages[request.messages.length - 1];
    const query = lastMessage?.content?.trim() || "";
    const hash = _hashString(query);
    const created = Math.floor(Date.now() / 1000);
    const id = `mock-${hash.toString(16)}`;

    const templates = [
      "According to the available documentation, this refers to ",
      "Based on the knowledge base, the answer is related to ",
      "The documents indicate that this concerns ",
    ];
    const template = templates[hash % templates.length];
    const answer = `${template}"${query.slice(0, 60)}". Please consult the cited sources for full details.`;
    const words = answer.split(/\s+/);

    // Yield role chunk
    yield {
      id,
      object: "chat.completion.chunk",
      created,
      model: request.model,
      choices: [{ index: 0, delta: { role: "assistant" }, finish_reason: null }],
    };

    // Yield content chunks word by word
    for (let i = 0; i < words.length; i++) {
      yield {
        id,
        object: "chat.completion.chunk",
        created,
        model: request.model,
        choices: [
          {
            index: 0,
            delta: { content: (i > 0 ? " " : "") + words[i] },
            finish_reason: null,
          },
        ],
      };
    }

    // Yield finish chunk
    yield {
      id,
      object: "chat.completion.chunk",
      created,
      model: request.model,
      choices: [{ index: 0, delta: {}, finish_reason: "stop" }],
    };
  }

  async embedding(request: EmbeddingRequest): Promise<EmbeddingResponse> {
    const inputs = Array.isArray(request.input) ? request.input : [request.input];

    return {
      object: "list",
      data: inputs.map((text, index) => ({
        object: "embedding",
        embedding: _deterministicEmbedding(text),
        index,
      })),
      model: request.model,
      usage: {
        prompt_tokens: inputs.reduce((sum, inp) => sum + inp.split(/\s+/).length, 0),
        total_tokens: inputs.reduce((sum, inp) => sum + inp.split(/\s+/).length, 0),
      },
    };
  }
}
