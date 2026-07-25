"use client";

import * as React from "react";

import { api } from "@/lib/api";
import type { DashboardResponse } from "@/lib/api/types";
import { describeError, isAbort } from "@/lib/errors";

interface DashboardPollingState {
  data: DashboardResponse | null;
  error: string | null;
  loading: boolean;
  refresh: () => void;
}

/**
 * Polling cada ~2 s, sin WebSockets (§1.2.8). Si una llamada falla se conserva
 * el último dato bueno: en medio del pitch es peor una pantalla en blanco que
 * un aviso de reintento.
 */
export function useDashboardPolling(intervalMs = 2000): DashboardPollingState {
  const [data, setData] = React.useState<DashboardResponse | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(true);

  const controllerRef = React.useRef<AbortController | null>(null);

  const load = React.useCallback(async () => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;

    try {
      const response = await api.dashboard(controller.signal);
      setData(response);
      setError(null);
    } catch (cause) {
      if (!isAbort(cause)) setError(describeError(cause));
    } finally {
      if (!controller.signal.aborted) setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void load();
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") void load();
    }, intervalMs);

    return () => {
      window.clearInterval(timer);
      controllerRef.current?.abort();
    };
  }, [intervalMs, load]);

  return { data, error, loading, refresh: () => void load() };
}
