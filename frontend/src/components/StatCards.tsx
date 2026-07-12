import { AlertTriangle, CheckCircle2, Clock3, Gauge, Inbox } from 'lucide-react';
import { StatsOverview } from '../api/client';
import { useI18n } from '../i18n';

type Props = {
  stats: StatsOverview | null;
};

const empty = {
  total_tickets: 0,
  resolved_tickets: 0,
  escalated_tickets: 0,
  pending_approval_count: 0,
  average_latency: 0,
  escalation_rate: 0
};

function StatCards({ stats }: Props) {
  const { t } = useI18n();
  const data = stats ?? empty;
  const cards = [
    { label: t('dashboard.totalTickets'), value: data.total_tickets, icon: Inbox, tone: 'text-slate-700' },
    { label: t('dashboard.resolved'), value: data.resolved_tickets, icon: CheckCircle2, tone: 'text-ocean' },
    { label: t('dashboard.escalated'), value: data.escalated_tickets, icon: AlertTriangle, tone: 'text-rosewood' },
    { label: t('dashboard.pendingApproval'), value: data.pending_approval_count, icon: Clock3, tone: 'text-ember' },
    { label: t('dashboard.averageLatency'), value: `${data.average_latency} ms`, icon: Gauge, tone: 'text-slate-700' }
  ];
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <section key={card.label} className="panel p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-medium uppercase text-slate-500">{card.label}</p>
                <p className="mt-2 text-2xl font-semibold text-ink">{card.value}</p>
              </div>
              <Icon className={`h-5 w-5 ${card.tone}`} aria-hidden="true" />
            </div>
          </section>
        );
      })}
    </div>
  );
}

export default StatCards;
