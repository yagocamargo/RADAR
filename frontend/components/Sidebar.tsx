"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Radar as RadarIcon,
  Building2,
  BarChart3,
  Bell,
  FileText,
  ShieldCheck,
  Sun,
  Moon,
  LogOut,
} from "lucide-react";
import clsx from "clsx";
import { useAuth } from "@/lib/auth-context";
import { useTheme } from "@/lib/theme-context";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/hunting", label: "Hunting", icon: RadarIcon },
  { href: "/empresas", label: "Ecossistema", icon: Building2 },
  { href: "/mercado", label: "Mercado", icon: BarChart3 },
  { href: "/alertas", label: "Alertas", icon: Bell },
  { href: "/relatorios", label: "Relatorios", icon: FileText },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    api
      .get("/api/v1/alertas?filtro=nao_lidos")
      .then((data) => setUnread(data.unread_count || 0))
      .catch(() => {});
  }, [pathname]);

  const canSeeAdmin = user?.role === "admin" || user?.role === "manager";

  return (
    <aside className="w-60 shrink-0 h-screen sticky top-0 flex flex-col border-r border-border bg-surface">
      <div className="px-5 py-5 flex items-center gap-2 border-b border-border">
        <RadarIcon size={20} className="text-accent" />
        <span className="font-semibold tracking-tight text-[15px]">Radar</span>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const active = pathname?.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors relative",
                active
                  ? "bg-accent/10 text-accent font-medium"
                  : "text-muted hover:bg-background hover:text-foreground"
              )}
            >
              <Icon size={17} />
              {item.label}
              {item.href === "/alertas" && unread > 0 && (
                <span className="ml-auto bg-critical text-white text-[10px] font-semibold rounded-full px-1.5 py-0.5 min-w-[18px] text-center">
                  {unread}
                </span>
              )}
            </Link>
          );
        })}

        {canSeeAdmin && (
          <Link
            href="/admin"
            className={clsx(
              "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
              pathname?.startsWith("/admin")
                ? "bg-accent/10 text-accent font-medium"
                : "text-muted hover:bg-background hover:text-foreground"
            )}
          >
            <ShieldCheck size={17} />
            Admin
          </Link>
        )}
      </nav>

      <div className="px-3 pb-3">
        <button
          onClick={toggleTheme}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm text-muted hover:bg-background hover:text-foreground transition-colors"
        >
          {theme === "light" ? <Moon size={17} /> : <Sun size={17} />}
          {theme === "light" ? "Tema escuro" : "Tema claro"}
        </button>
      </div>

      <div className="px-4 py-4 border-t border-border">
        <div className="flex items-center justify-between gap-2">
          <div className="min-w-0">
            <p className="text-sm font-medium truncate">{user?.name}</p>
            <p className="text-xs text-muted truncate capitalize">{user?.role}</p>
          </div>
          <button
            onClick={logout}
            title="Sair"
            className="p-2 rounded-md text-muted hover:bg-background hover:text-critical transition-colors shrink-0"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </aside>
  );
}
