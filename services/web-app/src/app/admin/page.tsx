"use client";

import { useState, useEffect } from "react";
import type { UserRole } from "@/types";
import { fetchApi } from "@/lib/api";

interface AdminUser {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  created_at: string;
}

export default function AdminPage(): JSX.Element {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [services, setServices] = useState<Array<{ service: string; status: string; response_time_ms: number }>>([]);
  const [apiKeyName, setApiKeyName] = useState<string>("");
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [userData, healthData] = await Promise.all([
          fetchApi<{ users: AdminUser[] }>("/admin/users"),
          fetchApi<{ services: Array<{ service: string; status: string; response_time_ms: number }> }>("/admin/health"),
        ]);
        setUsers(userData.users || []);
        setServices(healthData.services || []);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load admin data");
        setLoading(false);
      }
    })();
  }, []);

  const handleGenerateKey = async (): Promise<void> => {
    if (!apiKeyName.trim()) return;
    try {
      const data = await fetchApi<{ key: string }>("/admin/keys", {
        method: "POST",
        body: JSON.stringify({ name: apiKeyName.trim() }),
      });
      setGeneratedKey(data.key);
      setApiKeyName("");
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate API key");
    }
  };

  if (loading) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">Admin</h1>
        <div className="flex items-center justify-center py-16">
          <div className="animate-spin h-8 w-8 border-4 border-brand-600 border-t-transparent rounded-full" />
          <span className="ml-3 text-gray-500">Loading admin panel...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">Admin</h1>
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-700 dark:text-red-400">
          <p className="font-semibold">Error loading admin panel</p>
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
      <h1 className="text-2xl font-bold mb-6">Admin</h1>

      <section className="card mb-6">
        <h2 className="text-lg font-semibold mb-4">System Health</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {services.map((service) => (
              <div key={service.service} className="text-center p-3 rounded bg-gray-50 dark:bg-gray-800">
                <div className="text-sm text-gray-500">{service.service}</div>
                <div
                  className={`font-semibold mt-1 ${
                    service.status === "healthy" ? "text-green-500" : "text-red-500"
                  }`}
                >
                  {service.status}
                </div>
                <div className="text-xs text-gray-400 mt-1">{service.response_time_ms}ms</div>
              </div>
          ))}
        </div>
      </section>

      <section className="card mb-6">
        <h2 className="text-lg font-semibold mb-4">Users</h2>
        {users.length === 0 ? (
          <p className="text-gray-500 text-sm">No users loaded. Connect to the API to manage users.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2">Name</th>
                <th className="text-left py-2">Email</th>
                <th className="text-left py-2">Role</th>
                <th className="text-left py-2">Created</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="border-b">
                  <td className="py-2">{user.name}</td>
                  <td className="py-2">{user.email}</td>
                  <td className="py-2">
                    <span className="px-2 py-0.5 rounded bg-brand-100 text-brand-700 text-xs">{user.role}</span>
                  </td>
                  <td className="py-2">{new Date(user.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="card">
        <h2 className="text-lg font-semibold mb-4">API Keys</h2>
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            placeholder="Key name"
            value={apiKeyName}
            onChange={(e) => setApiKeyName(e.target.value)}
            className="input max-w-xs"
          />
          <button className="btn-primary" disabled={!apiKeyName} onClick={handleGenerateKey}>
            Generate Key
          </button>
        </div>
        {generatedKey && (
          <div className="mb-4 rounded border border-green-200 bg-green-50 p-3 text-sm text-green-700 dark:border-green-800 dark:bg-green-900/20 dark:text-green-300">
            Generated key: <span className="font-mono">{generatedKey}</span>
          </div>
        )}
        <p className="text-gray-500 text-sm">Generate API keys for programmatic access to the platform.</p>
      </section>
    </div>
  );
}
