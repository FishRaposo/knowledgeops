"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard" },
  { href: "/chat", label: "Chat" },
  { href: "/documents", label: "Documents" },
  { href: "/evals", label: "Evaluations" },
  { href: "/traces", label: "Traces" },
  { href: "/costs", label: "Costs" },
  { href: "/admin", label: "Admin" },
];

export function Sidebar(): JSX.Element {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-screen w-[260px] border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-4">
      <div className="mb-8">
        <h1 className="text-xl font-bold text-brand-600">KnowledgeOps</h1>
        <p className="text-xs text-gray-500 mt-1">AI Knowledge Platform</p>
      </div>

      <nav className="space-y-1">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`block px-3 py-2 rounded-md text-sm transition-colors ${
                isActive
                  ? "bg-brand-50 text-brand-700 font-medium dark:bg-brand-900/20 dark:text-brand-400"
                  : "text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-900"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="absolute bottom-4 left-4 right-4">
        <div className="text-xs text-gray-400">
          <p>KnowledgeOps v0.1.0</p>
          <p className="mt-1">Open Source</p>
        </div>
      </div>
    </aside>
  );
}
