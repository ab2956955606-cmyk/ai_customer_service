import { LucideIcon, ServerCog } from 'lucide-react';
import { ReactNode } from 'react';

export type NavItem = {
  id: string;
  label: string;
  icon: LucideIcon;
};

type LayoutProps = {
  items: NavItem[];
  activePage: string;
  onNavigate: (page: string) => void;
  health: Record<string, string> | null;
  children: ReactNode;
};

function Layout({ items, activePage, onNavigate, health, children }: LayoutProps) {
  const online = health?.status === 'ok';
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-slate-200 bg-white lg:block">
        <div className="flex h-16 items-center border-b border-slate-200 px-5">
          <div>
            <div className="text-base font-semibold tracking-normal text-ink">SupportOps Agent</div>
            <div className="text-xs text-slate-500">Agentic support console</div>
          </div>
        </div>
        <nav className="space-y-1 p-3">
          {items.map((item) => {
            const Icon = item.icon;
            const active = item.id === activePage;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onNavigate(item.id)}
                className={`flex w-full items-center gap-3 px-3 py-2 text-sm font-medium transition ${
                  active
                    ? 'bg-teal-50 text-ocean'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`}
                style={{ borderRadius: 8 }}
                title={item.label}
              >
                <Icon className="h-4 w-4" aria-hidden="true" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
          <div className="flex min-h-16 flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between lg:px-6">
            <div>
              <h1 className="text-lg font-semibold text-ink">{items.find((item) => item.id === activePage)?.label}</h1>
              <p className="text-sm text-slate-500">Multi-step workflow, tools, approvals, retrieval, trace, evals.</p>
            </div>
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className={`badge ${online ? 'border-teal-200 bg-teal-50 text-ocean' : 'border-rose-200 bg-rose-50 text-rosewood'}`}>
                <ServerCog className="h-3.5 w-3.5" aria-hidden="true" />
                {health?.status ?? 'checking'}
              </span>
              <span className="badge border-slate-200 bg-slate-50 text-slate-600">LLM {health?.llm_provider ?? 'mock'}</span>
              <span className="badge border-slate-200 bg-slate-50 text-slate-600">RAG {health?.retriever ?? 'unknown'}</span>
            </div>
          </div>
          <div className="flex gap-1 overflow-x-auto border-t border-slate-100 p-2 lg:hidden">
            {items.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onNavigate(item.id)}
                  className={`btn shrink-0 ${activePage === item.id ? 'border-ocean text-ocean' : ''}`}
                  title={item.label}
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
        </header>
        <main className="px-4 py-5 lg:px-6">{children}</main>
      </div>
    </div>
  );
}

export default Layout;
