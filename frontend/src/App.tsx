import { useCallback, useEffect, useState } from 'react';
import { Activity, CheckSquare, Database, Gauge, Inbox } from 'lucide-react';
import Layout, { NavItem } from './components/Layout';
import DashboardPage from './pages/DashboardPage';
import TicketsPage from './pages/TicketsPage';
import ApprovalsPage from './pages/ApprovalsPage';
import KnowledgePage from './pages/KnowledgePage';
import EvalsPage from './pages/EvalsPage';
import { api, StatsOverview } from './api/client';
import { useI18n } from './i18n';

function App() {
  const { t } = useI18n();
  const [page, setPage] = useState('dashboard');
  const [stats, setStats] = useState<StatsOverview | null>(null);
  const [health, setHealth] = useState<Record<string, string> | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [deepSeekApiKey, setDeepSeekApiKey] = useState<string | null>(null);

  const refresh = useCallback(() => setRefreshKey((value) => value + 1), []);
  const navItems: NavItem[] = [
    { id: 'dashboard', label: t('nav.dashboard'), icon: Gauge },
    { id: 'tickets', label: t('nav.tickets'), icon: Inbox },
    { id: 'approvals', label: t('nav.approvals'), icon: CheckSquare },
    { id: 'knowledge', label: t('nav.knowledge'), icon: Database },
    { id: 'evals', label: t('nav.evals'), icon: Activity }
  ];

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

  useEffect(() => {
    function clearEphemeralKey() {
      setDeepSeekApiKey(null);
    }
    window.addEventListener('pagehide', clearEphemeralKey);
    return () => window.removeEventListener('pagehide', clearEphemeralKey);
  }, []);

  return (
    <Layout
      items={navItems}
      activePage={page}
      onNavigate={setPage}
      health={health}
      deepSeekConfigured={Boolean(deepSeekApiKey)}
      onDeepSeekKeySave={setDeepSeekApiKey}
      onDeepSeekKeyClear={() => setDeepSeekApiKey(null)}
    >
      {page === 'dashboard' && <DashboardPage stats={stats} onRefresh={refresh} />}
      {page === 'tickets' && <TicketsPage onChanged={refresh} deepSeekApiKey={deepSeekApiKey} />}
      {page === 'approvals' && <ApprovalsPage onChanged={refresh} />}
      {page === 'knowledge' && <KnowledgePage />}
      {page === 'evals' && <EvalsPage onChanged={refresh} deepSeekApiKey={deepSeekApiKey} />}
    </Layout>
  );
}

export default App;
