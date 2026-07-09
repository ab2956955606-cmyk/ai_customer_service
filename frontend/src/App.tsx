import { useCallback, useEffect, useState } from 'react';
import { Activity, CheckSquare, Database, Gauge, Inbox } from 'lucide-react';
import Layout, { NavItem } from './components/Layout';
import DashboardPage from './pages/DashboardPage';
import TicketsPage from './pages/TicketsPage';
import ApprovalsPage from './pages/ApprovalsPage';
import KnowledgePage from './pages/KnowledgePage';
import EvalsPage from './pages/EvalsPage';
import { api, StatsOverview } from './api/client';

const navItems: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: Gauge },
  { id: 'tickets', label: 'Tickets', icon: Inbox },
  { id: 'approvals', label: 'Approvals', icon: CheckSquare },
  { id: 'knowledge', label: 'Knowledge', icon: Database },
  { id: 'evals', label: 'Evals', icon: Activity }
];

function App() {
  const [page, setPage] = useState('dashboard');
  const [stats, setStats] = useState<StatsOverview | null>(null);
  const [health, setHealth] = useState<Record<string, string> | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const refresh = useCallback(() => setRefreshKey((value) => value + 1), []);

  useEffect(() => {
    Promise.all([api.stats(), api.health()])
      .then(([statsPayload, healthPayload]) => {
        setStats(statsPayload);
        setHealth(healthPayload);
      })
      .catch(() => {
        setHealth({ status: 'offline', db: 'unknown', llm_provider: 'mock', retriever: 'unknown' });
      });
  }, [refreshKey]);

  return (
    <Layout items={navItems} activePage={page} onNavigate={setPage} health={health}>
      {page === 'dashboard' && <DashboardPage stats={stats} onRefresh={refresh} />}
      {page === 'tickets' && <TicketsPage onChanged={refresh} />}
      {page === 'approvals' && <ApprovalsPage onChanged={refresh} />}
      {page === 'knowledge' && <KnowledgePage />}
      {page === 'evals' && <EvalsPage onChanged={refresh} />}
    </Layout>
  );
}

export default App;
