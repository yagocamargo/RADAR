"use client";

import { useEffect, useState } from "react";
import { Database, Users, Bell, Building2, FileSignature, Trash2, Play } from "lucide-react";
import ProtectedShell from "@/components/ProtectedShell";
import MetricCard from "@/components/MetricCard";
import { api, ApiError } from "@/lib/api";

type AdminStats = {
  stats: {
    total_empresas: number;
    total_contratos: number;
    total_sinais: number;
    total_usuarios: number;
    alertas_nao_lidos: number;
  };
  redis: { status: string; used_memory_human: string | null };
};

const AGENTS = [
  { key: "enriquecimento", label: "Enriquecimento", endpoint: "/api/v1/admin/agentes/enriquecimento" },
  { key: "monitoramento", label: "Monitoramento", endpoint: "/api/v1/admin/agentes/monitoramento" },
  { key: "alertas", label: "Alertas", endpoint: "/api/v1/admin/agentes/alertas" },
  { key: "pncp", label: "Coleta PNCP", endpoint: "/api/v1/admin/agentes/pncp" },
];

export default function AdminPage() {
  const [data, setData] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);
  const [triggering, setTriggering] = useState<string | null>(null);

  function load() {
    api
      .get<AdminStats>("/api/v1/admin/stats")
      .then(setData)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 403) {
          setMessage("Acesso restrito a administradores e gestores.");
        }
      })
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function triggerAgent(key: string, endpoint: string) {
    setTriggering(key);
    try {
      await api.post(endpoint);
      setMessage(`Agente de ${key} disparado com sucesso.`);
    } catch {
      setMessage(`Falha ao disparar o agente de ${key}.`);
    } finally {
      setTriggering(null);
    }
  }

  async function clearCache() {
    const res = await api.post("/api/v1/admin/cache/limpar");
    setMessage(res.message);
    load();
  }

  if (message && !data) {
    return (
      <ProtectedShell>
        <p className="text-sm text-critical">{message}</p>
      </ProtectedShell>
    );
  }

  return (
    <ProtectedShell>
      <div className="mb-6">
        <h1 className="text-xl font-semibold tracking-tight">Admin</h1>
        <p className="text-sm text-muted">Estatisticas do sistema e agentes de coleta</p>
      </div>

      {loading || !data ? (
        <p className="text-sm text-muted">Carregando estatisticas...</p>
      ) : (
        <div className="flex flex-col gap-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <MetricCard label="Empresas" value={data.stats.total_empresas} icon={<Building2 size={16} className="text-muted" />} />
            <MetricCard label="Contratos" value={data.stats.total_contratos} icon={<FileSignature size={16} className="text-muted" />} />
            <MetricCard label="Sinais" value={data.stats.total_sinais} icon={<Database size={16} className="text-muted" />} />
            <MetricCard label="Usuarios" value={data.stats.total_usuarios} icon={<Users size={16} className="text-muted" />} />
            <MetricCard label="Alertas nao lidos" value={data.stats.alertas_nao_lidos} icon={<Bell size={16} className="text-muted" />} />
          </div>

          {message && (
            <p className="text-sm bg-accent/10 text-accent rounded-md px-3 py-2">{message}</p>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card p-5">
              <h2 className="text-sm font-semibold mb-4">Disparar agentes manualmente</h2>
              <div className="flex flex-col gap-2">
                {AGENTS.map((a) => (
                  <button
                    key={a.key}
                    onClick={() => triggerAgent(a.key, a.endpoint)}
                    disabled={triggering === a.key}
                    className="flex items-center justify-between text-sm px-3 py-2 rounded-md border border-border hover:bg-background transition-colors disabled:opacity-60"
                  >
                    <span>{a.label}</span>
                    <Play size={13} className={triggering === a.key ? "animate-pulse" : ""} />
                  </button>
                ))}
              </div>
            </div>

            <div className="card p-5">
              <h2 className="text-sm font-semibold mb-4">Redis</h2>
              <div className="flex flex-col gap-2 text-sm mb-4">
                <div className="flex justify-between">
                  <span className="text-muted">Status</span>
                  <span className={data.redis.status === "conectado" ? "text-green-600" : "text-critical"}>
                    {data.redis.status}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted">Memoria usada</span>
                  <span>{data.redis.used_memory_human || "—"}</span>
                </div>
              </div>
              <button
                onClick={clearCache}
                className="flex items-center gap-2 text-sm px-3 py-2 rounded-md border border-border hover:bg-critical/10 hover:text-critical hover:border-critical/30 transition-colors"
              >
                <Trash2 size={14} /> Limpar cache
              </button>
            </div>
          </div>
        </div>
      )}
    </ProtectedShell>
  );
}
