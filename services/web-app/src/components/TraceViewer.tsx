"use client";

import { useEffect, useMemo, useState } from "react";
import type { TraceSpan } from "../types";
import { fetchApi } from "../lib/api";

export function TraceViewer(): JSX.Element {
  const [traces, setTraces] = useState<TraceSpan[]>([]);
  const [selectedTrace, setSelectedTrace] = useState<string>("");
  const [serviceFilter, setServiceFilter] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  const handleRefresh = async (): Promise<void> => {
    try {
      const path = serviceFilter ? `/traces?service=${encodeURIComponent(serviceFilter)}` : "/traces";
      const data = await fetchApi<{ traces: TraceSpan[] }>(path);
      setTraces(data.traces || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch traces");
    }
  };

  useEffect(() => {
    void handleRefresh();
  }, []);

  const services = useMemo(
    () => Array.from(new Set(traces.map((trace) => trace.service))).sort(),
    [traces]
  );

  return (
    <div>
      <div className="flex flex-wrap items-center gap-4 mb-6">
        <select
          value={serviceFilter}
          onChange={(event) => setServiceFilter(event.target.value)}
          className="input max-w-xs"
        >
          <option value="">All services</option>
          {services.map((service) => (
            <option key={service} value={service}>
              {service}
            </option>
          ))}
        </select>
        <button onClick={handleRefresh} className="btn-primary">
          Refresh Traces
        </button>
        <span className="text-sm text-gray-500">{traces.length} traces</span>
      </div>

      {error && (
        <div className="mb-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-300">
          {error}
        </div>
      )}

      {traces.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500">No traces collected yet.</p>
          <p className="text-gray-400 text-sm mt-1">
            Traces will appear here after you run queries or evaluations.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {traces.map((trace) => {
            const duration = new Date(trace.end_time).getTime() - new Date(trace.start_time).getTime();
            return (
              <div
                key={trace.span_id}
                className={`card cursor-pointer hover:border-brand-400 ${
                  selectedTrace === trace.span_id ? "border-brand-500" : ""
                }`}
                onClick={() => setSelectedTrace(trace.span_id)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-xs font-mono bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded">
                      {trace.service}
                    </span>
                    <span className="ml-2 text-sm">{trace.operation}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-500">{duration}ms</span>
                    <span className="text-xs text-gray-400 font-mono">{trace.trace_id.slice(0, 8)}</span>
                  </div>
                </div>
                {selectedTrace === trace.span_id && (
                  <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-gray-500">Trace ID:</span> {trace.trace_id}
                      </div>
                      <div>
                        <span className="text-gray-500">Span ID:</span> {trace.span_id}
                      </div>
                      <div>
                        <span className="text-gray-500">Start:</span>{" "}
                        {new Date(trace.start_time).toLocaleString()}
                      </div>
                      <div>
                        <span className="text-gray-500">Duration:</span> {duration}ms
                      </div>
                    </div>
                    {Object.keys(trace.attributes).length > 0 && (
                      <div className="mt-2">
                        <span className="text-gray-500 text-sm">Attributes:</span>
                        <pre className="text-xs bg-gray-50 dark:bg-gray-800 p-2 rounded mt-1 overflow-x-auto">
                          {JSON.stringify(trace.attributes, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
