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
import { Building2, TrendingUp, FileSignature, Flame, Search } from "lucide-react";
import ProtectedShell from "@/components/ProtectedShell";
import MetricCard from "@/components/MetricCard";
import { api } from "@/lib/api";

type DashboardData = {
  metrics: {
    total_empresas: number;
    empresas_em_expansao: number;
    contratos_do_mes: number;
    indice_aquecimento: number;
  };
  top_growth: { id: string; slug: string; nome_fantasia: string; uf: string; growth_signal: number; vagas_abertas_30d: number }[];
  signal_feed: { id: string; company_nome: string; type: string; title: string; uf: string | null; signal_date: string }[];
  activity_by_segment: { segment: string; count: number }[];
};

const SIGNAL_LABELS: Record<string, string> = {
  vaga_aberta: "Vaga aberta",
  novo_contrato: "Novo contrato",
  expansao: "Expansao",
  publicacao_diario_oficial: "Diario Oficial",
  noticia: "Noticia",
};

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<DashboardData>("/api/v1/dashboard")
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  return (
    <ProtectedShell>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted">Visao geral do mercado GovTech monitorado</p>
        </div>
        <Link
          href="/hunting"
          className="flex items-center gap-2 bg-accent text-accent-foreground text-sm font-medium px-4 py-2 rounded-md hover:opacity-90 transition-opacity"
        >
          <Search size={15} />
          Nova busca de hunting
        </Link>
      </div>

      {loading || !data ? (
        <p className="text-sm text-muted">Carregando dados do mercado...</p>
      ) : (
        <div className="flex flex-col gap-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard label="Empresas monitoradas" value={data.metrics.total_empresas} icon={<Building2 size={16} className="text-muted" />} />
            <MetricCard label="Em expansao" value={data.metrics.empresas_em_expansao} icon={<TrendingUp size={16} className="text-muted" />} />
            <MetricCard label="Contratos do mes" value={data.metrics.contratos_do_mes} icon={<FileSignature size={16} className="text-muted" />} />
            <MetricCard label="Indice de aquecimento" value={`${data.metrics.indice_aquecimento}%`} icon={<Flame size={16} className="text-muted" />} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="card p-5 lg:col-span-1">
              <h2 className="text-sm font-semibold mb-4">Maior crescimento recente</h2>
              <div className="flex flex-col gap-3">
                {data.top_growth.map((c) => (
                  <Link
                    key={c.id}
                    href={`/empresas/${c.slug}`}
                    className="flex items-center justify-between hover:bg-background rounded-md px-2 py-1.5 -mx-2 transition-colors"
                  >
                    <div>
                      <p className="text-sm font-medium">{c.nome_fantasia}</p>
                      <p className="text-xs text-muted">{c.uf} · {c.vagas_abertas_30d} vagas/30d</p>
                    </div>
                    <span className="text-xs font-semibold text-accent">
                      {Math.round(c.growth_signal * 100)}%
                    </span>
                  </Link>
                ))}
              </div>
            </div>

            <div className="card p-5 lg:col-span-1">
              <h2 className="text-sm font-semibold mb-4">Ultimos sinais de mercado</h2>
              <div className="flex flex-col gap-3 max-h-72 overflow-y-auto">
                {data.signal_feed.map((s) => (
                  <div key={s.id} className="text-sm">
                    <p className="font-medium leading-snug">{s.title}</p>
                    <p className="text-xs text-muted">
                      {SIGNAL_LABELS[s.type] || s.type} · {s.uf || "—"} · {new Date(s.signal_date).toLocaleDateString("pt-BR")}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="card p-5 lg:col-span-1">
              <h2 className="text-sm font-semibold mb-4">Atividade por segmento</h2>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={data.activity_by_segment} layout="vertical" margin={{ left: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--border)" />
                  <XAxis type="number" hide />
                  <YAxis
                    type="category"
                    dataKey="segment"
                    width={110}
                    tick={{ fontSize: 11, fill: "var(--muted)" }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", fontSize: 12 }}
                  />
                  <Bar dataKey="count" fill="var(--accent)" radius={[0, 4, 4, 0]} barSize={12} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </ProtectedShell>
  );
}
