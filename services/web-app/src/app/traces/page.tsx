"use client";

import { useState, useEffect } from "react";
import { TraceViewer } from "@/components/TraceViewer";

export default function TracesPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch("/api/traces");
        if (!res.ok) throw new Error("Failed to load traces");
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load traces");
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">Traces</h1>
        <div className="flex items-center justify-center py-16">
          <div className="animate-spin h-8 w-8 border-4 border-brand-600 border-t-transparent rounded-full" />
          <span className="ml-3 text-gray-500">Loading traces...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">Traces</h1>
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-700 dark:text-red-400">
          <p className="font-semibold">Error loading traces</p>
          <p className="text-sm mt-1">{error}</p>
          <button onClick={() => window.location.reload()} className="btn-primary mt-3 text-sm">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Traces</h1>
      <TraceViewer />
    </div>
  );
}
