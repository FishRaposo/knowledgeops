"use client";

import { useState, useEffect } from "react";
import { DocumentManager } from "@/components/DocumentManager";
import { fetchApi } from "@/lib/api";

export default function DocumentsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        await fetchApi("/documents");
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load documents");
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">Documents</h1>
        <div className="flex items-center justify-center py-16">
          <div className="animate-spin h-8 w-8 border-4 border-brand-600 border-t-transparent rounded-full" />
          <span className="ml-3 text-gray-500">Loading documents...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">Documents</h1>
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-700 dark:text-red-400">
          <p className="font-semibold">Error loading documents</p>
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
      <h1 className="text-2xl font-bold mb-6">Documents</h1>
      <DocumentManager />
    </div>
  );
}
