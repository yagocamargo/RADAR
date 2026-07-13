"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Search } from "lucide-react";
import ProtectedShell from "@/components/ProtectedShell";
import { MomentumBadge } from "@/components/MetricCard";
import { api } from "@/lib/api";

type CompanyItem = {
  id: string;
  slug: string;
  nome_fantasia: string;
  cnpj: string;
  uf: string;
  cidade: string;
  municipios_atendidos: number;
  contratos_ativos: number;
  vagas_abertas_30d: number;
  e_concorrente: boolean;
  momentum: string;
  segments: { id: string; name: string }[];
};

const UFS = ["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"];
const PAGE_SIZE = 20;

export default function EmpresasPage() {
  const [search, setSearch] = useState("");
  const [uf, setUf] = useState("");
  const [concorrente, setConcorrente] = useState<string>("");
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<CompanyItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (uf) params.set("uf", uf);
    if (concorrente) params.set("concorrente", concorrente);
    params.set("page", String(page));
    params.set("page_size", String(PAGE_SIZE));

    const timeout = setTimeout(() => {
      api
        .get(`/api/v1/empresas?${params.toString()}`)
        .then((data) => {
          setItems(data.items);
          setTotal(data.total);
        })
        .finally(() => setLoading(false));
    }, 300);

    return () => clearTimeout(timeout);
  }, [search, uf, concorrente, page]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <ProtectedShell>
      <div className="mb-6">
        <h1 className="text-xl font-semibold tracking-tight">Ecossistema</h1>
        <p className="text-sm text-muted">{total} empresas monitoradas no ecossistema GovTech</p>
      </div>

      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="flex-1 flex items-center gap-2 px-3 border border-border rounded-md bg-surface">
          <Search size={15} className="text-muted shrink-0" />
          <input
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Buscar por nome ou CNPJ..."
            className="w-full py-2 bg-transparent text-sm outline-none"
          />
        </div>
        <select
          value={uf}
          onChange={(e) => { setUf(e.target.value); setPage(1); }}
          className="px-3 py-2 rounded-md bg-surface border border-border text-sm outline-none"
        >
          <option value="">Todos os estados</option>
          {UFS.map((u) => <option key={u} value={u}>{u}</option>)}
        </select>
        <select
          value={concorrente}
          onChange={(e) => { setConcorrente(e.target.value); setPage(1); }}
          className="px-3 py-2 rounded-md bg-surface border border-border text-sm outline-none"
        >
          <option value="">Todas as empresas</option>
          <option value="true">Somente concorrentes</option>
          <option value="false">Nao concorrentes</option>
        </select>
      </div>

      {loading ? (
        <p className="text-sm text-muted">Carregando empresas...</p>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mb-6">
            {items.map((c) => (
              <Link key={c.id} href={`/empresas/${c.slug}`} className="card p-4 hover:border-accent/50 transition-colors">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-sm font-semibold">{c.nome_fantasia}</h3>
                  <MomentumBadge momentum={c.momentum} />
                </div>
                <p className="text-xs text-muted mb-3">{c.cidade}/{c.uf} {c.e_concorrente && "· Concorrente"}</p>

                <div className="flex flex-wrap gap-1.5 mb-3">
                  {c.segments.slice(0, 3).map((s) => (
                    <span key={s.id} className="text-[10px] font-medium bg-accent/10 text-accent px-2 py-0.5 rounded-full">
                      {s.name}
                    </span>
                  ))}
                </div>

                <div className="flex items-center justify-between text-xs text-muted border-t border-border pt-3">
                  <span>{c.municipios_atendidos} municipios</span>
                  <span>{c.contratos_ativos} contratos</span>
                  <span>{c.vagas_abertas_30d} vagas/30d</span>
                </div>
              </Link>
            ))}
          </div>

          <div className="flex items-center justify-center gap-3">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
              className="px-3 py-1.5 text-sm rounded-md border border-border disabled:opacity-40"
            >
              Anterior
            </button>
            <span className="text-sm text-muted">Pagina {page} de {totalPages}</span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="px-3 py-1.5 text-sm rounded-md border border-border disabled:opacity-40"
            >
              Proxima
            </button>
          </div>
        </>
      )}
    </ProtectedShell>
  );
}
