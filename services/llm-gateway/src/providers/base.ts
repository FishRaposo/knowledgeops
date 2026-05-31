/** Base LLM provider interface. */

export interface ChatCompletionResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Array<{
    index: number;
    message: { role: string; content: string };
    finish_reason: string;
  }>;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface EmbeddingResponse {
  object: string;
  data: Array<{
    object: string;
    embedding: number[];
    index: number;
  }>;
  model: string;
  usage: {
    prompt_tokens: number;
    total_tokens: number;
  };
}

export interface ChatCompletionRequest {
  model: string;
  messages: Array<{ role: string; content: string }>;
  temperature?: number;
  max_tokens?: number;
}

export interface EmbeddingRequest {
  model: string;
  input: string | string[];
}

export interface LLMProvider {
  chatCompletion(request: ChatCompletionRequest): Promise<ChatCompletionResponse>;
  embedding(request: EmbeddingRequest): Promise<EmbeddingResponse>;
  name: string;
}
