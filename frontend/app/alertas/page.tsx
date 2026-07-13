"use client";

import { useEffect, useState } from "react";
import ProtectedShell from "@/components/ProtectedShell";
import { PriorityDot } from "@/components/MetricCard";
import { api } from "@/lib/api";

type AlertItem = {
  id: string;
  title: string;
  body: string;
  type: string;
  priority: string;
  status: string;
  created_at: string;
};

const FILTERS = [
  { value: "todos", label: "Todos" },
  { value: "nao_lidos", label: "Nao lidos" },
  { value: "lidos", label: "Lidos" },
  { value: "acionados", label: "Acionados" },
];

export default function AlertasPage() {
  const [filter, setFilter] = useState("todos");
  const [items, setItems] = useState<AlertItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    api
      .get(`/api/v1/alertas?filtro=${filter}`)
      .then((data) => {
        setItems(data.items);
        setUnreadCount(data.unread_count);
      })
      .finally(() => setLoading(false));
  }

  useEffect(load, [filter]);

  async function markAsRead(id: string) {
    await api.patch(`/api/v1/alertas/${id}/marcar-lido`);
    load();
  }

  async function markAllAsRead() {
    await api.post("/api/v1/alertas/marcar-todos-lidos");
    load();
  }

  return (
    <ProtectedShell>
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">
            Alertas {unreadCount > 0 && <span className="text-critical text-base">({unreadCount} nao lidos)</span>}
          </h1>
          <p className="text-sm text-muted">Notificacoes personalizadas de sinais de mercado</p>
        </div>
        <button
          onClick={markAllAsRead}
          className="text-sm px-3 py-2 rounded-md border border-border hover:bg-background transition-colors"
        >
          Marcar todos como lidos
        </button>
      </div>

      <div className="flex gap-2 mb-5">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`text-sm px-3 py-1.5 rounded-full border transition-colors ${
              filter === f.value ? "bg-accent text-accent-foreground border-accent" : "border-border text-muted hover:text-foreground"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="text-sm text-muted">Carregando alertas...</p>
      ) : items.length === 0 ? (
        <p className="text-sm text-muted">Nenhum alerta encontrado para este filtro.</p>
      ) : (
        <div className="flex flex-col gap-2">
          {items.map((a) => (
            <button
              key={a.id}
              onClick={() => a.status === "nao_lido" && markAsRead(a.id)}
              className="card p-4 text-left hover:border-accent/40 transition-colors"
            >
              <div className="flex items-start gap-3">
                <div className="mt-1.5">
                  <PriorityDot priority={a.priority} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium">{a.title}</p>
                    <span className="text-xs text-muted shrink-0">
                      {new Date(a.created_at).toLocaleDateString("pt-BR")}
                    </span>
                  </div>
                  <p className="text-sm text-muted mt-1">{a.body}</p>
                  <span className="text-[10px] uppercase tracking-wide text-muted mt-2 inline-block">
                    {a.status.replace("_", " ")}
                  </span>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </ProtectedShell>
  );
}
