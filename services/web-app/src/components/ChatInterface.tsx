"use client";

import { useState } from "react";
import type { QueryResponse, Citation } from "../types";
import { fetchApi } from "../lib/api";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  refusal?: boolean;
}

export function ChatInterface(): JSX.Element {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: ChatMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);
    const query = input;

    try {
      const data = await fetchApi<QueryResponse>("/query", {
        method: "POST",
        body: JSON.stringify({ query, top_k: 5 }),
      });
      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: data.answer,
        citations: data.citations,
        refusal: data.refusal,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch {
      const errorMessage: ChatMessage = {
        role: "assistant",
        content: "Sorry, an error occurred while processing your query.",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-20">
            <p className="text-lg">Ask a question about your knowledge base</p>
            <p className="text-sm mt-2">Answers will include citations to source documents.</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[70%] rounded-lg p-4 ${
                msg.role === "user"
                  ? "bg-brand-600 text-white"
                  : "bg-gray-100 dark:bg-gray-800"
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
              {msg.refusal && (
                <p className="text-xs text-amber-600 mt-2">This query was outside the knowledge base scope.</p>
              )}
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                  <p className="text-xs font-semibold mb-1">Sources:</p>
                  {msg.citations.map((citation, cidx) => (
                    <div key={cidx} className="text-xs text-gray-500 mt-1">
                      <span className="font-medium">{citation.document_title}</span>: {citation.excerpt.slice(0, 100)}
                      ...
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-4">
              <p className="text-gray-500">Thinking...</p>
            </div>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question..."
          className="input flex-1"
          disabled={loading}
        />
        <button type="submit" className="btn-primary" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
