"use client";

import { useEffect, useState, useRef } from "react";
import type { Document, DocumentStatus } from "../types";
import { fetchApi } from "../lib/api";

export function DocumentManager(): JSX.Element {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadDocuments = async (): Promise<void> => {
    try {
      const data = await fetchApi<{ documents: Document[] }>("/documents");
      setDocuments(data.documents || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load documents");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadDocuments();
  }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>): Promise<void> => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const data = await fetchApi<{ document: Document }>("/documents/upload", {
        method: "POST",
        body: formData,
      });
      setDocuments((prev) => [data.document, ...prev]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const statusColors: Record<DocumentStatus, string> = {
    pending: "bg-yellow-100 text-yellow-700",
    processing: "bg-blue-100 text-blue-700",
    completed: "bg-green-100 text-green-700",
    failed: "bg-red-100 text-red-700",
  };

  return (
    <div>
      <div className="mb-6">
        <label className="btn-primary cursor-pointer inline-block">
          {uploading ? "Uploading..." : "Upload Document"}
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.md,.html,.htm,.docx"
            onChange={handleUpload}
            className="hidden"
            disabled={uploading}
          />
        </label>
        <span className="text-sm text-gray-500 ml-3">PDF, Markdown, HTML, DOCX</span>
      </div>

      {error && (
        <div className="mb-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-300">
          {error}
        </div>
      )}

      {loading ? (
        <div className="card text-center py-12">
          <p className="text-gray-500">Loading documents...</p>
        </div>
      ) : documents.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500">No documents uploaded yet.</p>
          <p className="text-gray-400 text-sm mt-1">Upload a document to start building your knowledge base.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {documents.map((doc) => (
            <div key={doc.id} className="card flex items-center justify-between">
              <div>
                <h3 className="font-medium">{doc.title}</h3>
                <p className="text-sm text-gray-500">{doc.source}</p>
              </div>
              <div className="flex items-center gap-3">
                <span className={`px-2 py-0.5 rounded text-xs ${statusColors[doc.status]}`}>
                  {doc.status}
                </span>
                <span className="text-xs text-gray-400">v{doc.version}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
