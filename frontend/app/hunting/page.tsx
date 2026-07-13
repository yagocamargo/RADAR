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
  LineChart,
  Line,
  CartesianGrid,
} from "recharts";
import { Search, Bookmark, Sparkles, Clock } from "lucide-react";
import ProtectedShell from "@/components/ProtectedShell";
import { api, ApiError } from "@/lib/api";

type HuntingResult = {
  query_id: string;
  interpreted_segments: string[];
  interpreted_uf: string | null;
  companies: {
    id: string;
    slug: string;
    nome_fantasia: string;
    uf: string;
    cidade: string;
    municipios_atendidos: number;
    vagas_abertas_30d: number;
    score: number;
  }[];
  regional_concentration: Record<string, number>;
  trend_last_12_months: { month: string; vagas: number }[];
  ai_summary: string | null;
  ai_suggestions: string[];
  ai_enabled: boolean;
};

type HistoryItem = { id: string; query_text: string; saved: boolean; monitoring_active: boolean; created_at: string };

const UFS = ["", "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"];

export default function HuntingPage() {
  const [query, setQuery] = useState("");
  const [uf, setUf] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<HuntingResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);

  useEffect(() => {
    api.get<HistoryItem[]>("/api/v1/hunting/historico").then(setHistory).catch(() => {});
  }, []);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.post<HuntingResult>("/api/v1/hunting", { query, uf: uf || undefined });
      setResult(data);
      api.get<HistoryItem[]>("/api/v1/hunting/historico").then(setHistory).catch(() => {});
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erro ao processar a busca.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveQuery() {
    if (!result) return;
    await api.post("/api/v1/hunting/salvar", { query_id: result.query_id, monitoring_active: true });
    api.get<HistoryItem[]>("/api/v1/hunting/historico").then(setHistory).catch(() => {});
  }

  const regionData = result
    ? Object.entries(result.regional_concentration)
        .map(([uf, count]) => ({ uf, count }))
        .sort((a, b) => b.count - a.count)
    : [];

  return (
    <ProtectedShell>
      <div className="mb-6">
        <h1 className="text-xl font-semibold tracking-tight">Hunting</h1>
        <p className="text-sm text-muted">Descreva o perfil que voce busca e receba empresas ranqueadas por aderencia</p>
      </div>

      <form onSubmit={handleSearch} className="card p-4 flex flex-col sm:flex-row gap-3 mb-6">
        <div className="flex-1 flex items-center gap-2 px-3 border border-border rounded-md bg-background">
          <Search size={16} className="text-muted shrink-0" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ex: Analista de Implantacao de Tributos em SC"
            className="w-full py-2 bg-transparent text-sm outline-none"
          />
        </div>
        <select
          value={uf}
          onChange={(e) => setUf(e.target.value)}
          className="px-3 py-2 rounded-md bg-background border border-border text-sm outline-none"
        >
          <option value="">Todos os estados</option>
          {UFS.filter(Boolean).map((u) => (
            <option key={u} value={u}>{u}</option>
          ))}
        </select>
        <button
          type="submit"
          disabled={loading}
          className="bg-accent text-accent-foreground text-sm font-medium px-5 py-2 rounded-md hover:opacity-90 disabled:opacity-60"
        >
          {loading ? "Buscando..." : "Buscar"}
        </button>
      </form>

      {error && <p className="text-sm text-critical bg-critical/10 rounded-md px-3 py-2 mb-4">{error}</p>}

      {!result && !loading && (
        <div className="card p-5">
          <h2 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <Clock size={14} /> Historico de consultas
          </h2>
          {history.length === 0 ? (
            <p className="text-sm text-muted">Nenhuma consulta realizada ainda.</p>
          ) : (
            <div className="flex flex-col gap-2">
              {history.map((h) => (
                <button
                  key={h.id}
                  onClick={() => setQuery(h.query_text)}
                  className="text-left text-sm px-2 py-1.5 -mx-2 rounded-md hover:bg-background transition-colors"
                >
                  {h.query_text}
                  {h.saved && <Bookmark size={12} className="inline ml-2 text-accent" />}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {result && (
        <div className="flex flex-col gap-6">
          {!result.ai_enabled && (
            <p className="text-xs text-muted bg-background border border-border rounded-md px-3 py-2">
              Chave da OpenAI nao configurada — usando busca por palavras-chave como fallback.
            </p>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 card p-5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-semibold">
                  Empresas ranqueadas
                  {result.interpreted_segments.length > 0 && (
                    <span className="text-muted font-normal"> · {result.interpreted_segments.join(", ")}</span>
                  )}
                </h2>
                <button
                  onClick={handleSaveQuery}
                  className="flex items-center gap-1.5 text-xs text-accent hover:underline"
                >
                  <Bookmark size={13} /> Salvar e monitorar
                </button>
              </div>

              <div className="flex flex-col divide-y divide-border">
                {result.companies.map((c, idx) => (
                  <Link
                    key={c.id}
                    href={`/empresas/${c.slug}`}
                    className="flex items-center justify-between py-3 hover:bg-background -mx-2 px-2 rounded-md transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-muted w-5">{idx + 1}</span>
                      <div>
                        <p className="text-sm font-medium">{c.nome_fantasia}</p>
                        <p className="text-xs text-muted">
                          {c.cidade}/{c.uf} · {c.municipios_atendidos} municipios · {c.vagas_abertas_30d} vagas/30d
                        </p>
                      </div>
                    </div>
                    <span className="text-sm font-semibold text-accent">{Math.round(c.score * 100)}%</span>
                  </Link>
                ))}
              </div>
            </div>

            <div className="flex flex-col gap-6">
              <div className="card p-5">
                <h2 className="text-sm font-semibold mb-3 flex items-center gap-2">
                  <Sparkles size={14} /> Resumo do mercado
                </h2>
                <p className="text-sm text-muted leading-relaxed">
                  {result.ai_summary || "Resumo de IA indisponivel para esta busca."}
                </p>
              </div>

              <div className="card p-5">
                <h2 className="text-sm font-semibold mb-3">Sugestoes de acao</h2>
                <ul className="text-sm text-muted flex flex-col gap-2 list-disc list-inside">
                  {result.ai_suggestions.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card p-5">
              <h2 className="text-sm font-semibold mb-4">Concentracao regional</h2>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={regionData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                  <XAxis dataKey="uf" tick={{ fontSize: 11, fill: "var(--muted)" }} axisLine={false} tickLine={false} />
                  <YAxis hide />
                  <Tooltip contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", fontSize: 12 }} />
                  <Bar dataKey="count" fill="var(--accent)" radius={[4, 4, 0, 0]} barSize={20} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="card p-5">
              <h2 className="text-sm font-semibold mb-4">Tendencia de vagas (12 meses)</h2>
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={result.trend_last_12_months}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="month" tick={{ fontSize: 10, fill: "var(--muted)" }} axisLine={false} tickLine={false} />
                  <YAxis hide />
                  <Tooltip contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", fontSize: 12 }} />
                  <Line type="monotone" dataKey="vagas" stroke="var(--accent)" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </ProtectedShell>
  );
}
