"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Sparkles, RefreshCw, Search, MapPin, Building2, Briefcase, Flame } from "lucide-react";
import ProtectedShell from "@/components/ProtectedShell";
import { MomentumBadge } from "@/components/MetricCard";
import { api } from "@/lib/api";

type CompanyDetail = {
  id: string;
  slug: string;
  nome_fantasia: string;
  razao_social: string;
  cnpj: string;
  uf: string;
  cidade: string;
  endereco: string | null;
  municipios_atendidos: number;
  contratos_ativos: number;
  vagas_abertas_30d: number;
  vagas_abertas_90d: number;
  relevance_score: number;
  growth_signal: number;
  profile_completeness: number;
  e_concorrente: boolean;
  e_monitorada: boolean;
  e_verificada: boolean;
  momentum: string;
  ai_summary: string | null;
  ai_summary_updated_at: string | null;
  segments: { id: string; name: string; confidence_score: number }[];
};

type SignalItem = { id: string; type: string; title: string; description: string | null; uf: string | null; signal_date: string };
type CompetitorItem = { id: string; slug: string; nome_fantasia: string; uf: string; momentum: string };

const TABS = ["Visao geral", "Linha do tempo", "Concorrentes"] as const;

export default function CompanyDetailPage() {
  const params = useParams<{ slug: string }>();
  const router = useRouter();
  const [company, setCompany] = useState<CompanyDetail | null>(null);
  const [timeline, setTimeline] = useState<SignalItem[]>([]);
  const [competitors, setCompetitors] = useState<CompetitorItem[]>([]);
  const [tab, setTab] = useState<(typeof TABS)[number]>("Visao geral");
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (!params?.slug) return;
    setLoading(true);
    api.get<CompanyDetail>(`/api/v1/empresas/${params.slug}`).then(setCompany).finally(() => setLoading(false));
  }, [params?.slug]);

  useEffect(() => {
    if (!params?.slug) return;
    if (tab === "Linha do tempo" && timeline.length === 0) {
      api.get<SignalItem[]>(`/api/v1/empresas/${params.slug}/timeline`).then(setTimeline).catch(() => {});
    }
    if (tab === "Concorrentes" && competitors.length === 0) {
      api.get<CompetitorItem[]>(`/api/v1/empresas/${params.slug}/concorrentes`).then(setCompetitors).catch(() => {});
    }
  }, [tab, params?.slug]);

  async function handleGenerateSummary() {
    if (!params?.slug) return;
    setGenerating(true);
    try {
      const updated = await api.post<CompanyDetail>(`/api/v1/empresas/${params.slug}/gerar-resumo`);
      setCompany(updated);
    } finally {
      setGenerating(false);
    }
  }

  function startHuntingFromCompany() {
    if (!company) return;
    router.push(`/hunting?ref=${company.slug}`);
  }

  if (loading || !company) {
    return (
      <ProtectedShell>
        <p className="text-sm text-muted">Carregando ficha da empresa...</p>
      </ProtectedShell>
    );
  }

  return (
    <ProtectedShell>
      <div className="flex items-start justify-between mb-6 flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-xl font-semibold tracking-tight">{company.nome_fantasia}</h1>
            <MomentumBadge momentum={company.momentum} />
            {company.e_concorrente && (
              <span className="text-xs font-medium bg-critical/10 text-critical px-2 py-0.5 rounded-full">Concorrente</span>
            )}
            {company.e_monitorada && (
              <span className="text-xs font-medium bg-accent/10 text-accent px-2 py-0.5 rounded-full">Monitorada</span>
            )}
          </div>
          <p className="text-sm text-muted mt-1">
            {company.cnpj} · {company.cidade}/{company.uf}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleGenerateSummary}
            disabled={generating}
            className="flex items-center gap-2 text-sm px-3 py-2 rounded-md border border-border hover:bg-background transition-colors disabled:opacity-60"
          >
            <RefreshCw size={14} className={generating ? "animate-spin" : ""} />
            {generating ? "Gerando..." : "Atualizar resumo de IA"}
          </button>
          <button
            onClick={startHuntingFromCompany}
            className="flex items-center gap-2 text-sm px-3 py-2 rounded-md bg-accent text-accent-foreground hover:opacity-90 transition-opacity"
          >
            <Search size={14} />
            Hunting a partir daqui
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="card p-4 flex items-center gap-3">
          <MapPin size={16} className="text-muted" />
          <div>
            <p className="text-xs text-muted">Municipios atendidos</p>
            <p className="text-lg font-semibold">{company.municipios_atendidos}</p>
          </div>
        </div>
        <div className="card p-4 flex items-center gap-3">
          <Building2 size={16} className="text-muted" />
          <div>
            <p className="text-xs text-muted">Contratos ativos</p>
            <p className="text-lg font-semibold">{company.contratos_ativos}</p>
          </div>
        </div>
        <div className="card p-4 flex items-center gap-3">
          <Briefcase size={16} className="text-muted" />
          <div>
            <p className="text-xs text-muted">Vagas / 30 dias</p>
            <p className="text-lg font-semibold">{company.vagas_abertas_30d}</p>
          </div>
        </div>
        <div className="card p-4 flex items-center gap-3">
          <Flame size={16} className="text-muted" />
          <div>
            <p className="text-xs text-muted">Momento de mercado</p>
            <p className="text-lg font-semibold capitalize">{company.momentum}</p>
          </div>
        </div>
      </div>

      <div className="flex gap-1 border-b border-border mb-5">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === t ? "border-accent text-accent" : "border-transparent text-muted hover:text-foreground"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "Visao geral" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 card p-5">
            <h2 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <Sparkles size={14} /> Resumo gerado por IA
            </h2>
            <p className="text-sm text-muted leading-relaxed">
              {company.ai_summary || "Nenhum resumo gerado ainda. Clique em 'Atualizar resumo de IA'."}
            </p>
          </div>
          <div className="card p-5">
            <h2 className="text-sm font-semibold mb-3">Segmentos identificados</h2>
            <div className="flex flex-col gap-2">
              {company.segments.map((s) => (
                <div key={s.id} className="flex items-center justify-between text-sm">
                  <span>{s.name}</span>
                  <span className="text-xs text-muted">{Math.round(s.confidence_score * 100)}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {tab === "Linha do tempo" && (
        <div className="card p-5">
          {timeline.length === 0 ? (
            <p className="text-sm text-muted">Nenhum evento registrado.</p>
          ) : (
            <div className="flex flex-col divide-y divide-border">
              {timeline.map((s) => (
                <div key={s.id} className="py-3">
                  <p className="text-sm font-medium">{s.title}</p>
                  <p className="text-xs text-muted">{new Date(s.signal_date).toLocaleDateString("pt-BR")} · {s.uf || "—"}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === "Concorrentes" && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {competitors.length === 0 ? (
            <p className="text-sm text-muted">Nenhum concorrente direto identificado.</p>
          ) : (
            competitors.map((c) => (
              <a key={c.id} href={`/empresas/${c.slug}`} className="card p-4 hover:border-accent/50 transition-colors">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium">{c.nome_fantasia}</p>
                  <MomentumBadge momentum={c.momentum} />
                </div>
                <p className="text-xs text-muted mt-1">{c.uf}</p>
              </a>
            ))
          )}
        </div>
      )}
    </ProtectedShell>
  );
}
