import { Ticket } from '../api/client';
import { useI18n } from '../i18n';

type Props = {
  tickets: Ticket[];
  selectedId: number | null;
  onSelect: (id: number) => void;
};

const statusTone: Record<string, string> = {
  resolved: 'border-teal-200 bg-teal-50 text-ocean',
  escalated: 'border-rose-200 bg-rose-50 text-rosewood',
  pending_approval: 'border-amber-200 bg-amber-50 text-ember',
  failed: 'border-rose-200 bg-rose-50 text-rosewood'
};

function TicketList({ tickets, selectedId, onSelect }: Props) {
  const { t, label } = useI18n();
  return (
    <section className="panel overflow-hidden">
      <div className="border-b border-slate-200 p-4">
        <h2 className="text-sm font-semibold text-ink">{t('tickets.title')}</h2>
      </div>
      <div className="max-h-[620px] divide-y divide-slate-100 overflow-y-auto">
        {tickets.map((ticket) => (
          <button
            key={ticket.id}
            type="button"
            onClick={() => onSelect(ticket.id)}
            className={`block w-full px-4 py-3 text-left transition hover:bg-slate-50 ${
              selectedId === ticket.id ? 'bg-teal-50' : 'bg-white'
            }`}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-ink">{ticket.subject}</p>
                <p className="mt-1 truncate text-xs text-slate-500">{ticket.customer_email ?? t('common.unknownCustomer')}</p>
              </div>
              <span className={`badge shrink-0 ${statusTone[ticket.status] ?? 'border-slate-200 bg-slate-50 text-slate-600'}`}>
                {label(ticket.status)}
              </span>
            </div>
            <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">
              <span>{label(ticket.category)}</span>
              <span>{label(ticket.priority ?? 'normal')}</span>
              <span>{t('common.risk')}: {label(ticket.risk_level ?? 'low')}</span>
            </div>
          </button>
        ))}
        {tickets.length === 0 && <p className="p-4 text-sm text-slate-500">{t('tickets.empty')}</p>}
      </div>
    </section>
  );
}

export default TicketList;
