import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { Inbox, BookOpen, Activity, Settings as SettingsIcon, Sparkles, PlusCircle, LogOut, UserCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth";

const items = [
  { to: "/inbox", label: "Inbox", icon: Inbox },
  { to: "/inbox/new", label: "New ticket", icon: PlusCircle },
  { to: "/kb", label: "Knowledge base", icon: BookOpen },
  { to: "/metrics", label: "Metrics", icon: Activity },
  { to: "/settings", label: "Settings", icon: SettingsIcon },
];

export default function Layout() {
  const { username, signOut } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    signOut();
    navigate("/login", { replace: true });
  };

  return (
    <div className="grid grid-cols-[260px_1fr] grid-rows-[56px_1fr] h-full">
      <aside className="row-span-2 bg-[color:var(--color-bg-1)] border-r border-[color:var(--color-line)] flex flex-col">
        <div className="px-5 py-4 flex items-center gap-2 border-b border-[color:var(--color-line)]">
          <Sparkles size={18} className="text-[color:var(--color-mint)]" />
          <div className="leading-tight">
            <div className="text-[13px] font-semibold tracking-tight">Emoti CS Agent</div>
            <div className="text-[11px] text-[color:var(--color-fg-muted)]">operator console</div>
          </div>
        </div>
        <nav className="flex-1 py-3">
          {items.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-5 py-2.5 text-[13.5px]",
                  isActive
                    ? "text-[color:var(--color-mint)] bg-[color:var(--color-mint)]/5 border-l-2 border-[color:var(--color-mint)]"
                    : "text-[color:var(--color-fg-muted)] hover:text-[color:var(--color-fg)] hover:bg-[color:var(--color-bg-2)] border-l-2 border-transparent"
                )
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="px-5 py-4 border-t border-[color:var(--color-line)] text-[11px] text-[color:var(--color-fg-dim)]">
          <div>tenant: emoti</div>
          <div>v0.1.0 · demo build</div>
        </div>
      </aside>

      <header className="col-start-2 bg-[color:var(--color-bg-1)] border-b border-[color:var(--color-line)] flex items-center px-6 gap-4">
        <div className="text-[13px] text-[color:var(--color-fg-muted)]">
          Wyjątkowy Prezent · semi-autonomous CS pipeline · Polish
        </div>
        <div className="ml-auto flex items-center gap-3 text-[12px] text-[color:var(--color-fg-dim)]">
          <span className="inline-flex items-center gap-1.5">
            <span className="size-2 rounded-full bg-[color:var(--color-mint)] shadow-[0_0_8px_rgba(0,229,160,0.7)]" />
            backend live
          </span>
          {username && (
            <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-md bg-[color:var(--color-bg-2)] border border-[color:var(--color-line)] text-[color:var(--color-fg-muted)]">
              <UserCircle2 size={13} />
              {username}
            </span>
          )}
          <button
            type="button"
            onClick={handleLogout}
            className="inline-flex items-center gap-1.5 px-2 py-1 rounded-md hover:bg-[color:var(--color-bg-2)] hover:text-[color:var(--color-fg)]"
            title="Wyloguj"
          >
            <LogOut size={13} />
            Wyloguj
          </button>
        </div>
      </header>

      <main className="col-start-2 overflow-y-auto p-6">
        <Outlet />
      </main>
    </div>
  );
}
