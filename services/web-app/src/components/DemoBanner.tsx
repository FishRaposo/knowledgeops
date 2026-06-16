"use client";

import { useEffect, useState } from "react";
import { isDemoMode, subscribeDemoMode } from "../lib/api";

/**
 * A sticky banner shown whenever the console is serving the offline demo
 * dataset (i.e. the backend API gateway is unreachable). It makes the
 * demo-mode fallback visible so reviewers know the data is illustrative.
 */
export function DemoBanner(): JSX.Element | null {
  const [active, setActive] = useState<boolean>(false);

  useEffect(() => {
    setActive(isDemoMode());
    return subscribeDemoMode(setActive);
  }, []);

  if (!active) return null;

  return (
    <div
      role="status"
      data-testid="demo-banner"
      className="sticky top-0 z-50 flex items-center justify-center gap-2 bg-amber-500/90 px-4 py-2 text-center text-xs font-semibold text-amber-950 shadow-md backdrop-blur"
    >
      <span className="inline-block h-2 w-2 rounded-full bg-amber-900 animate-pulse" />
      Demo mode — backend unavailable. Showing illustrative sample data.
    </div>
  );
}
