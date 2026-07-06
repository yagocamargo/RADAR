"use client";

import { useEffect, useRef, useState } from "react";
import { Plus, FileText } from "lucide-react";
import ProtectedShell from "@/components/ProtectedShell";
import { api } from "@/lib/api";

type ReportItem = {
  id: string;
  title: string;
  type: string;
  status: string;
  content: string | null;
  error_message: string | null;
  created_at: string;
};

const REPORT_TYPES = [
  { value: "mercado_mensal", label: "Mercado Mensal" },
  { value: "analise_segmento", label: "Analise de Segmento" },
  { value: "perfil_empresa", label: "Perfil de Empresa" },
  { value: "resumo_executivo", label: "Resumo Executivo" },
];

const STATUS_LABEL: Record<string, string> = {
  na_fila: "Na fila",
  gerando: "Gerando",
  pronto: "Pronto",
  falhou: "Falhou",
};

export default function RelatoriosPage() {
  const [items, setItems] = useState<ReportItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [type, setType] = useState(REPORT_TYPES[0].value);
  const [selected, setSelected] = useState<ReportItem | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  function load() {
    api.get<ReportItem[]>("/api/v1/relatorios").then(setItems).finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
  }, []);

  // Polling a cada 5s enquanto houver relatorios em processamento
  useEffect(() => {
    const hasPending = items.some((i) => i.status === "na_fila" || i.status === "gerando");
    if (hasPending && !pollRef.current) {
      pollRef.current = setInterval(load, 5000);
    }
    if (!hasPending && pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [items]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    await api.post("/api/v1/relatorios", { title, type });
    setTitle("");
    setShowForm(false);
    load();
  }

  return (
    <ProtectedShell>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Relatorios</h1>
          <p className="text-sm text-muted">Gerenciador de relatorios de inteligencia</p>
        </div>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="flex items-center gap-2 bg-accent text-accent-foreground text-sm font-medium px-4 py-2 rounded-md hover:opacity-90 transition-opacity"
        >
          <Plus size={15} /> Novo relatorio
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="card p-4 flex flex-col sm:flex-row gap-3 mb-6">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Titulo do relatorio"
            className="flex-1 px-3 py-2 rounded-md bg-background border border-border text-sm outline-none"
          />
          <select
            value={type}
            onChange={(e) => setType(e.target.value)}
            className="px-3 py-2 rounded-md bg-background border border-border text-sm outline-none"
          >
            {REPORT_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
          <button type="submit" className="bg-accent text-accent-foreground text-sm font-medium px-4 py-2 rounded-md hover:opacity-90">
            Solicitar
          </button>
        </form>
      )}

      {loading ? (
        <p className="text-sm text-muted">Carregando relatorios...</p>
      ) : items.length === 0 ? (
        <p className="text-sm text-muted">Nenhum relatorio solicitado ainda.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {items.map((r) => (
            <button
              key={r.id}
              onClick={() => setSelected(r)}
              className="card p-4 text-left hover:border-accent/40 transition-colors"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <FileText size={15} className="text-muted" />
                  <p className="text-sm font-medium">{r.title}</p>
                </div>
                <span
                  className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                    r.status === "pronto"
                      ? "bg-green-500/10 text-green-600"
                      : r.status === "falhou"
                      ? "bg-critical/10 text-critical"
                      : "bg-accent/10 text-accent"
                  }`}
                >
                  {STATUS_LABEL[r.status]}
                </span>
              </div>
              <p className="text-xs text-muted">
                {REPORT_TYPES.find((t) => t.value === r.type)?.label} · {new Date(r.created_at).toLocaleDateString("pt-BR")}
              </p>
            </button>
          ))}
        </div>
      )}

      {selected && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50" onClick={() => setSelected(null)}>
          <div className="card max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-lg font-semibold mb-1">{selected.title}</h2>
            <p className="text-xs text-muted mb-4">{STATUS_LABEL[selected.status]}</p>
            {selected.status === "pronto" ? (
              <pre className="text-sm whitespace-pre-wrap font-sans text-foreground">{selected.content}</pre>
            ) : selected.status === "falhou" ? (
              <p className="text-sm text-critical">{selected.error_message}</p>
            ) : (
              <p className="text-sm text-muted">O relatorio ainda esta sendo gerado...</p>
            )}
            <button
              onClick={() => setSelected(null)}
              className="mt-6 text-sm px-4 py-2 rounded-md border border-border hover:bg-background transition-colors"
            >
              Fechar
            </button>
          </div>
        </div>
      )}
    </ProtectedShell>
  );
}
