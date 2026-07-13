import { ReactNode } from "react";
import clsx from "clsx";

export default function MetricCard({
  label,
  value,
  icon,
  hint,
}: {
  label: string;
  value: string | number;
  icon?: ReactNode;
  hint?: string;
}) {
  return (
    <div className="card p-5 flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted font-medium uppercase tracking-wide">{label}</span>
        {icon}
      </div>
      <span className="text-2xl font-semibold tracking-tight">{value}</span>
      {hint && <span className="text-xs text-muted">{hint}</span>}
    </div>
  );
}

export function MomentumBadge({ momentum }: { momentum: string }) {
  const map: Record<string, { label: string; className: string }> = {
    crescendo: { label: "Crescendo", className: "bg-green-500/10 text-green-600" },
    estavel: { label: "Estavel", className: "bg-blue-500/10 text-blue-600" },
    retracao: { label: "Retracao", className: "bg-red-500/10 text-red-600" },
  };
  const item = map[momentum] || map.estavel;
  return (
    <span className={clsx("text-xs font-medium px-2 py-0.5 rounded-full", item.className)}>
      {item.label}
    </span>
  );
}

export function PriorityDot({ priority }: { priority: string }) {
  const colorMap: Record<string, string> = {
    critica: "bg-critical",
    alta: "bg-high",
    media: "bg-medium",
    baixa: "bg-gray-400",
  };
  return <span className={clsx("badge-dot", colorMap[priority] || "bg-gray-400")} />;
}
