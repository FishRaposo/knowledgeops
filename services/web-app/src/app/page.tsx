"use client";

import { useState, useEffect } from "react";
import { fetchApi } from "@/lib/api";

interface HealthSummary {
  status: string;
  services: Record<string, string>;
}

export default function Home() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthSummary | null>(null);
  const [hoveredCard, setHoveredCard] = useState<number | null>(null);

  useEffect(() => {
    (async () => {
      try {
        // fetchApi transparently falls back to demo data when the backend is
        // unreachable, so the dashboard still renders with no services running.
        const data = await fetchApi<HealthSummary>("/health");
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
      <div className="flex flex-col items-center justify-center py-24 text-slate-400 font-sans">
        <div className="animate-spin h-10 w-10 border-4 border-violet-500 border-t-transparent rounded-full" />
        <span className="ml-3 mt-4 text-sm font-semibold tracking-wide">Syncing KnowledgeOps clusters...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-lg mt-12 bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900/30 rounded-2xl p-8 text-center backdrop-blur-md shadow-xl">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-12 h-12 mx-auto text-rose-500 mb-4">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
        </svg>
        <h2 className="font-extrabold text-xl text-slate-900 dark:text-slate-100">Gateway Disconnection</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-2 leading-relaxed">
          {error}. Ensure the primary API Gateway service is active and running in your container ecosystem.
        </p>
        <button
          onClick={() => window.location.reload()}
          className="mt-6 rounded-xl bg-violet-600 px-6 py-2.5 text-xs font-bold text-white shadow-lg shadow-violet-600/30 transition-all hover:bg-violet-500 active:scale-95"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const actionsList = [
    { title: "Chat Module", desc: "Interact with grounded knowledge bases via SSE query retrieval with integrated citations.", href: "/chat", border: "hover:border-violet-500/50" },
    { title: "Document Vault", desc: "Ingest and manage files across PDF, HTML, MD, and DOCX templates.", href: "/documents", border: "hover:border-sky-500/50" },
    { title: "Evaluations Bench", desc: "Execute automated evaluations with semantic, citation, and LLM-as-judge engines.", href: "/evals", border: "hover:border-emerald-500/50" },
    { title: "Distributed Tracing", desc: "Monitor multi-layered span trees and telemetry pathways in real-time.", href: "/traces", border: "hover:border-pink-500/50" },
    { title: "FinOps Spendings", desc: "Aggregated LLM operational costs organized by microservice, model, and active token rates.", href: "/costs", border: "hover:border-amber-500/50" },
    { title: "Admin Console", desc: "Control RBAC policies, API keys creation, and cluster configurations.", href: "/admin", border: "hover:border-indigo-500/50" }
  ];

  return (
    <div className="font-sans text-slate-100 max-w-6xl mx-auto px-4 py-8">
      {/* Premium glowing header block */}
      <div className="relative mb-12 overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60 p-8 shadow-2xl backdrop-blur-md">
        <div className="absolute right-0 top-0 h-40 w-40 rounded-full bg-violet-500/10 blur-3xl" />
        <div className="absolute left-1/3 bottom-0 h-40 w-40 rounded-full bg-indigo-500/10 blur-3xl" />
        <div className="relative flex flex-col md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-slate-100 via-slate-200 to-indigo-400 bg-clip-text text-transparent">
              KnowledgeOps Platform
            </h1>
            <p className="mt-2 text-slate-400 text-sm max-w-2xl leading-relaxed">
              The reference microservices architecture for enterprise knowledge pipelines. Coordinate document processing, trace telemetry vectors, and monitor token spending.
            </p>
          </div>
          {health && (
            <div className="mt-4 md:mt-0 flex items-center gap-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 px-4 py-1 text-xs font-semibold text-emerald-400">
              <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399] animate-pulse" />
              <span className="uppercase tracking-wider">{health.status}</span>
            </div>
          )}
        </div>
      </div>

      {/* Main Feature Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
        {actionsList.map((act, index) => (
          <a
            key={index}
            href={act.href}
            onMouseEnter={() => setHoveredCard(index)}
            onMouseLeave={() => setHoveredCard(null)}
            className={`rounded-xl border border-slate-800/80 bg-slate-900/40 p-6 shadow-lg backdrop-blur-sm transition-all hover:-translate-y-1 hover:shadow-xl hover:bg-slate-900/60 cursor-pointer ${act.border}`}
          >
            <h2 className="text-lg font-bold text-slate-200 mb-2 transition-colors duration-200">
              {act.title}
            </h2>
            <p className="text-slate-400 text-xs leading-relaxed">
              {act.desc}
            </p>
          </a>
        ))}
      </div>

      {/* Sibling Showcase Projects Section */}
      <div>
        <div className="border-t border-slate-800/85 pt-10 mb-6">
          <h2 className="text-xl font-bold text-slate-200">
            Showcase Integrations (Sibling Portfolio)
          </h2>
          <p className="text-xs text-slate-500 mt-1 leading-relaxed">
            External showcase systems fully linked and monitored inside the unified KnowledgeOps platform ecosystem. 
            <span className="text-slate-400 italic ml-1 block mt-0.5">Note: These are sibling projects in the portfolio ecosystem.</span>
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          <a
            href={process.env.NEXT_PUBLIC_SHOWCASE_GROUNDTRUTH_URL || "http://localhost:3000"}
            target="_blank"
            rel="noopener noreferrer"
            className="group rounded-xl border border-slate-800 bg-slate-900/30 p-5 hover:border-emerald-500/30 hover:bg-slate-900/50 shadow-md transition-all hover:-translate-y-1"
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_8px_#10b981]" />
              <h3 className="font-bold text-sm text-slate-200 group-hover:text-emerald-400 transition-colors">GroundTruth</h3>
            </div>
            <p className="text-slate-400 text-[11px] leading-relaxed">
              RAG system with template detection, OCR parsing, and active approval workflows.
            </p>
            <div className="text-[10px] text-slate-600 font-semibold tracking-wider uppercase mt-4">API Port 3000</div>
          </a>

          <a
            href={process.env.NEXT_PUBLIC_SHOWCASE_LLMGATEWAY_URL || "http://localhost:3001"}
            target="_blank"
            rel="noopener noreferrer"
            className="group rounded-xl border border-slate-800 bg-slate-900/30 p-5 hover:border-sky-500/30 hover:bg-slate-900/50 shadow-md transition-all hover:-translate-y-1"
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="h-2 w-2 rounded-full bg-sky-500 shadow-[0_0_8px_#38bdf8]" />
              <h3 className="font-bold text-sm text-slate-200 group-hover:text-sky-400 transition-colors">LLM Gateway</h3>
            </div>
            <p className="text-slate-400 text-[11px] leading-relaxed">
              Highly secure LLM proxy with PII masking, cost-aware routers, and active circuit-breaker states.
            </p>
            <div className="text-[10px] text-slate-600 font-semibold tracking-wider uppercase mt-4">API Port 3001</div>
          </a>

          <a
            href={process.env.NEXT_PUBLIC_SHOWCASE_EVALFORGE_URL || "http://localhost:3002"}
            target="_blank"
            rel="noopener noreferrer"
            className="group rounded-xl border border-slate-800 bg-slate-900/30 p-5 hover:border-purple-500/30 hover:bg-slate-900/50 shadow-md transition-all hover:-translate-y-1"
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="h-2 w-2 rounded-full bg-purple-500 shadow-[0_0_8px_#8b5cf6]" />
              <h3 className="font-bold text-sm text-slate-200 group-hover:text-purple-400 transition-colors">EvalForge</h3>
            </div>
            <p className="text-slate-400 text-[11px] leading-relaxed">
              Ethical AI validation suites with semantic judges and code regression detectors.
            </p>
            <div className="text-[10px] text-slate-600 font-semibold tracking-wider uppercase mt-4">API Port 3002</div>
          </a>

          <a
            href={process.env.NEXT_PUBLIC_SHOWCASE_AGENTTRACE_URL || "http://localhost:3003"}
            target="_blank"
            rel="noopener noreferrer"
            className="group rounded-xl border border-slate-800 bg-slate-900/30 p-5 hover:border-pink-500/30 hover:bg-slate-900/50 shadow-md transition-all hover:-translate-y-1"
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="h-2 w-2 rounded-full bg-pink-500 shadow-[0_0_8px_#ec4899]" />
              <h3 className="font-bold text-sm text-slate-200 group-hover:text-pink-400 transition-colors">AgentTrace</h3>
            </div>
            <p className="text-slate-400 text-[11px] leading-relaxed">
              Trace observability SDK tracking multi-tenant correlation IDs and deep span hierarchies.
            </p>
            <div className="text-[10px] text-slate-600 font-semibold tracking-wider uppercase mt-4">API Port 3003</div>
          </a>
        </div>
      </div>
    </div>
  );
}
