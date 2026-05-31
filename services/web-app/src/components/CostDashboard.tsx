"use client";

import { useState, useEffect } from "react";
import type { AlertRecord, CostRecord, CostSummary } from "../types";
import { fetchApi } from "../lib/api";

export function CostDashboard(): JSX.Element {
  const [costs, setCosts] = useState<CostRecord[]>([]);
  const [summary, setSummary] = useState<CostSummary>({
    total_usd: 0,
    by_service: {},
    by_model: {},
    by_user: {},
    total_prompt_tokens: 0,
    total_completion_tokens: 0,
    costs: [],
  });
  const [alerts, setAlerts] = useState<AlertRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCosts = async () => {
      setLoading(true);
      try {
        const data = await fetchApi<CostSummary>("/costs");
        const alertData = await fetchApi<{ alerts: AlertRecord[] }>("/alerts");
        setCosts(data.costs || []);
        setSummary({
          total_usd: data.total_usd ?? 0,
          by_service: data.by_service ?? {},
          by_model: data.by_model ?? {},
          by_user: data.by_user ?? {},
          total_prompt_tokens: data.total_prompt_tokens ?? 0,
          total_completion_tokens: data.total_completion_tokens ?? 0,
          costs: data.costs ?? [],
        });
        setAlerts(alertData.alerts || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load costs");
      } finally {
        setLoading(false);
      }
    };
    fetchCosts();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="animate-spin h-8 w-8 border-4 border-brand-600 border-t-transparent rounded-full" />
        <span className="ml-3 text-gray-500">Loading cost data...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-700 dark:text-red-400">
        <p className="font-semibold">Error loading costs</p>
        <p className="text-sm mt-1">{error}</p>
        <button onClick={() => window.location.reload()} className="btn-primary mt-3 text-sm">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="card text-center">
          <p className="text-sm text-gray-500">Total Spend</p>
          <p className="text-2xl font-bold">${summary.total_usd.toFixed(4)}</p>
        </div>
        <div className="card text-center">
          <p className="text-sm text-gray-500">Prompt Tokens</p>
          <p className="text-2xl font-bold">{summary.total_prompt_tokens.toLocaleString()}</p>
        </div>
        <div className="card text-center">
          <p className="text-sm text-gray-500">Completion Tokens</p>
          <p className="text-2xl font-bold">{summary.total_completion_tokens.toLocaleString()}</p>
        </div>
        <div className="card text-center">
          <p className="text-sm text-gray-500">Requests</p>
          <p className="text-2xl font-bold">{costs.length.toLocaleString()}</p>
        </div>
      </div>

      {alerts.length > 0 && (
        <div className="mb-6 space-y-2">
          {alerts.map((alert, index) => (
            <div
              key={`${alert.type}-${index}`}
              className="rounded border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-900/20 dark:text-amber-300"
            >
              <span className="font-semibold capitalize">{alert.severity}:</span> {alert.message}
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <h3 className="font-semibold mb-3">Spend by Service</h3>
          {Object.keys(summary.by_service).length === 0 ? (
            <p className="text-gray-500 text-sm">No cost data yet.</p>
          ) : (
            <div className="space-y-2">
              {Object.entries(summary.by_service).map(([service, cost]) => (
                <div key={service} className="flex justify-between text-sm">
                  <span>{service}</span>
                  <span>${cost.toFixed(4)}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <h3 className="font-semibold mb-3">Spend by Model</h3>
          {Object.keys(summary.by_model).length === 0 ? (
            <p className="text-gray-500 text-sm">No cost data yet.</p>
          ) : (
            <div className="space-y-2">
              {Object.entries(summary.by_model).map(([model, cost]) => (
                <div key={model} className="flex justify-between text-sm">
                  <span>{model}</span>
                  <span>${cost.toFixed(4)}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <h3 className="font-semibold mb-3">Spend by User</h3>
          {Object.keys(summary.by_user).length === 0 ? (
            <p className="text-gray-500 text-sm">No user cost data yet.</p>
          ) : (
            <div className="space-y-2">
              {Object.entries(summary.by_user).map(([user, cost]) => (
                <div key={user} className="flex justify-between text-sm">
                  <span>{user}</span>
                  <span>${cost.toFixed(4)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {costs.length > 0 && (
        <div className="mt-6">
          <h3 className="font-semibold mb-3">Recent Requests</h3>
          <div className="card overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Service</th>
                  <th className="text-left py-2">Model</th>
                  <th className="text-right py-2">Prompt</th>
                  <th className="text-right py-2">Completion</th>
                  <th className="text-right py-2">Cost</th>
                  <th className="text-left py-2">Time</th>
                </tr>
              </thead>
              <tbody>
                {costs.slice(0, 50).map((cost) => (
                  <tr key={cost.id} className="border-b">
                    <td className="py-2">{cost.service}</td>
                    <td className="py-2 font-mono text-xs">{cost.model}</td>
                    <td className="py-2 text-right">{cost.prompt_tokens.toLocaleString()}</td>
                    <td className="py-2 text-right">{cost.completion_tokens.toLocaleString()}</td>
                    <td className="py-2 text-right">${cost.total_cost_usd.toFixed(6)}</td>
                    <td className="py-2 text-gray-500">{new Date(cost.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
