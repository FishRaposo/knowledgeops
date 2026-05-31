"use client";

import { useState } from "react";
import type { EvalRun } from "../types";
import { fetchApi } from "../lib/api";

export function EvalRunner(): JSX.Element {
  const [runs, setRuns] = useState<EvalRun[]>([]);
  const [running, setRunning] = useState<boolean>(false);
  const [selectedSuite, setSelectedSuite] = useState<string>("basic_rag");

  const handleRun = async (): Promise<void> => {
    setRunning(true);
    try {
      const data = await fetchApi<{ eval_run: EvalRun }>("/evals/run", {
        method: "POST",
        body: JSON.stringify({ suite_path: `data/sample/eval_suites/${selectedSuite}.yaml` }),
      });
      setRuns((prev) => [data.eval_run, ...prev]);
    } catch {
      console.error("Eval run failed");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div>
      <div className="flex items-center gap-4 mb-6">
        <select
          value={selectedSuite}
          onChange={(e) => setSelectedSuite(e.target.value)}
          className="input max-w-xs"
        >
          <option value="basic_rag">Basic RAG Suite</option>
        </select>
        <button onClick={handleRun} className="btn-primary" disabled={running}>
          {running ? "Running..." : "Run Evaluation"}
        </button>
      </div>

      {runs.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500">No evaluation runs yet.</p>
          <p className="text-gray-400 text-sm mt-1">Select an eval suite and click Run to evaluate your RAG pipeline.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {runs.map((run) => (
            <div key={run.id} className="card">
              <div className="flex items-center justify-between">
                <h3 className="font-medium">{run.name}</h3>
                <span
                  className={`px-2 py-0.5 rounded text-xs ${
                    run.status === "completed"
                      ? "bg-green-100 text-green-700"
                      : run.status === "running"
                        ? "bg-blue-100 text-blue-700"
                        : run.status === "failed"
                          ? "bg-red-100 text-red-700"
                          : "bg-yellow-100 text-yellow-700"
                  }`}
                >
                  {run.status}
                </span>
              </div>
              {run.started_at && (
                <p className="text-sm text-gray-500 mt-1">
                  Started: {new Date(run.started_at).toLocaleString()}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
