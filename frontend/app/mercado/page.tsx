"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import ProtectedShell from "@/components/ProtectedShell";
import MetricCard from "@/components/MetricCard";
import { api } from "@/lib/api";

type MercadoData = {
  kpis: { label: string; value: number; variation_pct: number }[];
  by_segment: { segment: string; count: number }[];
  by_region: { uf: string; count: number }[];
  top_growth: { id: string; slug: string; nome_fantasia: string; uf: string; growth_signal: number }[];
  recent_signals: { id: string; company_nome: string; type: string; title: string; uf: string | null; signal_date: string }[];
};

const SEGMENT_OPTIONS = [
  "", "tributos", "folha-de-pagamento", "licitacoes", "compras-publicas",
  "protocolo", "gestao-escolar", "saude-publica", "transparencia",
];

export default function MercadoPage() {
  const [data, setData] = useState<MercadoData | null>(null);
  const [segmento, setSegmento] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const params = segmento ? `?segmento=${segmento}` : "";
    api.get<MercadoData>(`/api/v1/mercado${params}`).then(setData).finally(() => setLoading(false));
  }, [segmento]);

  return (
    <ProtectedShell>
      <div className="mb-6">
        <h1 className="text-xl font-semibold tracking-tight">Mercado</h1>
        <p className="text-sm text-muted">Painel executivo de inteligencia de mercado</p>
      </div>

      {loading || !data ? (
        <p className="text-sm text-muted">Carregando dados de mercado...</p>
      ) : (
        <div className="flex flex-col gap-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {data.kpis.map((k) => (
              <MetricCard key={k.label} label={k.label} value={k.value} />
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card p-5">
              <h2 className="text-sm font-semibold mb-4">Empresas por segmento</h2>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={data.by_segment}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                  <XAxis dataKey="segment" tick={{ fontSize: 9, fill: "var(--muted)" }} angle={-30} textAnchor="end" height={60} axisLine={false} tickLine={false} />
                  <YAxis hide />
                  <Tooltip contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", fontSize: 12 }} />
                  <Bar dataKey="count" fill="var(--accent)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="card p-5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-semibold">Concentracao por estado</h2>
                <select
                  value={segmento}
                  onChange={(e) => setSegmento(e.target.value)}
                  className="text-xs px-2 py-1 rounded-md border border-border bg-background outline-none"
                >
                  <option value="">Todos os segmentos</option>
                  {SEGMENT_OPTIONS.filter(Boolean).map((s) => (
                    <option key={s} value={s}>{s.replace(/-/g, " ")}</option>
                  ))}
                </select>
              </div>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={data.by_region} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--border)" />
                  <XAxis type="number" hide />
                  <YAxis type="category" dataKey="uf" width={35} tick={{ fontSize: 11, fill: "var(--muted)" }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", fontSize: 12 }} />
                  <Bar dataKey="count" fill="var(--accent)" radius={[0, 4, 4, 0]} barSize={10} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card p-5">
              <h2 className="text-sm font-semibold mb-4">Ranking de crescimento</h2>
              <div className="flex flex-col gap-3">
                {data.top_growth.map((c, i) => (
                  <Link key={c.id} href={`/empresas/${c.slug}`} className="flex items-center justify-between hover:bg-background rounded-md px-2 py-1.5 -mx-2 transition-colors">
                    <span className="text-sm">{i + 1}. {c.nome_fantasia} <span className="text-muted text-xs">({c.uf})</span></span>
                    <span className="text-sm font-semibold text-accent">{Math.round(c.growth_signal * 100)}%</span>
                  </Link>
                ))}
              </div>
            </div>

            <div className="card p-5">
              <h2 className="text-sm font-semibold mb-4">Sinais recentes</h2>
              <div className="flex flex-col gap-3 max-h-72 overflow-y-auto">
                {data.recent_signals.map((s) => (
                  <div key={s.id} className="text-sm">
                    <p className="font-medium leading-snug">{s.title}</p>
                    <p className="text-xs text-muted">{s.uf || "—"} · {new Date(s.signal_date).toLocaleDateString("pt-BR")}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </ProtectedShell>
  );
}
