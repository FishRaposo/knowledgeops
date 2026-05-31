"use client";

import { useState, useEffect } from "react";

interface HealthSummary {
  status: string;
  services: Record<string, string>;
}

export default function Home() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthSummary | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch("/api/health");
        if (!res.ok) throw new Error("System unavailable");
        const data = await res.json();
        setHealth(data);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to connect to API");
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="animate-spin h-8 w-8 border-4 border-brand-600 border-t-transparent rounded-full" />
        <span className="ml-3 text-gray-500">Connecting to KnowledgeOps...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-700 dark:text-red-400">
        <h2 className="font-semibold text-lg">Connection Error</h2>
        <p className="text-sm mt-1">{error}</p>
        <p className="text-sm mt-2">Make sure the API gateway is running and accessible.</p>
        <button onClick={() => window.location.reload()} className="btn-primary mt-3 text-sm">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">KnowledgeOps</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            An open source reference architecture for internal AI knowledge tools.
          </p>
        </div>
        {health && (
          <div className="flex items-center gap-2 text-sm">
            <span className={`h-2.5 w-2.5 rounded-full ${health.status === "healthy" ? "bg-green-500" : "bg-yellow-500"}`} />
            <span className="text-gray-500">{health.status}</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <a href="/chat" className="card hover:border-brand-400 transition-colors">
          <h2 className="text-xl font-semibold mb-2">Chat</h2>
          <p className="text-gray-500 dark:text-gray-400 text-sm">
            Query your knowledge base with grounded retrieval and citations.
          </p>
        </a>

        <a href="/documents" className="card hover:border-brand-400 transition-colors">
          <h2 className="text-xl font-semibold mb-2">Documents</h2>
          <p className="text-gray-500 dark:text-gray-400 text-sm">
            Upload and manage documents across PDF, Markdown, HTML, and DOCX.
          </p>
        </a>

        <a href="/evals" className="card hover:border-brand-400 transition-colors">
          <h2 className="text-xl font-semibold mb-2">Evaluations</h2>
          <p className="text-gray-500 dark:text-gray-400 text-sm">
            Run automated RAG evaluations with semantic, citation, and refusal judges.
          </p>
        </a>

        <a href="/traces" className="card hover:border-brand-400 transition-colors">
          <h2 className="text-xl font-semibold mb-2">Traces</h2>
          <p className="text-gray-500 dark:text-gray-400 text-sm">
            Browse and inspect distributed traces across all services.
          </p>
        </a>

        <a href="/costs" className="card hover:border-brand-400 transition-colors">
          <h2 className="text-xl font-semibold mb-2">Costs</h2>
          <p className="text-gray-500 dark:text-gray-400 text-sm">
            Track LLM spending by service, model, and user.
          </p>
        </a>

        <a href="/admin" className="card hover:border-brand-400 transition-colors">
          <h2 className="text-xl font-semibold mb-2">Admin</h2>
          <p className="text-gray-500 dark:text-gray-400 text-sm">
            Manage users, API keys, and system configuration.
          </p>
        </a>
      </div>

      <div className="mt-10">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Connected Projects
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
          External services integrated into the KnowledgeOps platform.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <a
            href="http://localhost:3000"
            target="_blank"
            rel="noopener noreferrer"
            className="card hover:border-green-400 transition-colors"
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="h-2 w-2 rounded-full bg-green-500" />
              <h3 className="font-semibold">GroundTruth</h3>
            </div>
            <p className="text-gray-500 dark:text-gray-400 text-sm">
              RAG assistant with doc processing, OCR, and approval workflows.
            </p>
            <p className="text-xs text-gray-400 mt-2">Port 3000</p>
          </a>

          <a
            href="http://localhost:3001"
            target="_blank"
            rel="noopener noreferrer"
            className="card hover:border-blue-400 transition-colors"
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="h-2 w-2 rounded-full bg-blue-500" />
              <h3 className="font-semibold">LLM Gateway</h3>
            </div>
            <p className="text-gray-500 dark:text-gray-400 text-sm">
              LLM proxy with guardrails, routing, and cost analytics.
            </p>
            <p className="text-xs text-gray-400 mt-2">Port 3001</p>
          </a>

          <a
            href="http://localhost:3002"
            target="_blank"
            rel="noopener noreferrer"
            className="card hover:border-purple-400 transition-colors"
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="h-2 w-2 rounded-full bg-purple-500" />
              <h3 className="font-semibold">EvalForge</h3>
            </div>
            <p className="text-gray-500 dark:text-gray-400 text-sm">
              AI evaluation harness with compliance rule packs.
            </p>
            <p className="text-xs text-gray-400 mt-2">Port 3002</p>
          </a>

          <a
            href="http://localhost:3003"
            target="_blank"
            rel="noopener noreferrer"
            className="card hover:border-orange-400 transition-colors"
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="h-2 w-2 rounded-full bg-orange-500" />
              <h3 className="font-semibold">AgentTrace</h3>
            </div>
            <p className="text-gray-500 dark:text-gray-400 text-sm">
              Distributed tracing and cost attribution for agent runs.
            </p>
            <p className="text-xs text-gray-400 mt-2">Port 3003</p>
          </a>
        </div>
      </div>
    </div>
  );
}
