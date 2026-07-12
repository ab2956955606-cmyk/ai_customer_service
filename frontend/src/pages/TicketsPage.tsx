import { useEffect, useState } from 'react';
import { RefreshCcw } from 'lucide-react';
import { api, Ticket, TicketDetail, TicketWorkflowResponse } from '../api/client';
import TicketForm from '../components/TicketForm';
import TicketList from '../components/TicketList';
import TicketDetailPage from './TicketDetailPage';
import { useI18n } from '../i18n';

type Props = {
  onChanged: () => void;
  deepSeekApiKey: string | null;
};

function TicketsPage({ onChanged, deepSeekApiKey }: Props) {
  const { t } = useI18n();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<TicketDetail | null>(null);
  const [created, setCreated] = useState<TicketWorkflowResponse | null>(null);

  function loadTickets() {
    api.tickets().then((items) => {
      setTickets(items);
      if (!selectedId && items.length > 0) {
        setSelectedId(items[0].id);
      }
    });
  }

  useEffect(() => {
    loadTickets();
  }, []);

  useEffect(() => {
    if (selectedId) {
      api.ticket(selectedId).then((payload) => {
        setDetail(payload);
        setCreated(null);
      });
    }
  }, [selectedId]);

  function onCreated(response: TicketWorkflowResponse) {
    setCreated(response);
    setDetail(null);
    setSelectedId(response.ticket.id);
    loadTickets();
    onChanged();
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[360px_1fr]">
      <div className="grid content-start gap-4">
        <TicketForm onCreated={onCreated} deepSeekApiKey={deepSeekApiKey} />
        <button type="button" className="btn" onClick={loadTickets} title={t('tickets.refresh')}>
          <RefreshCcw className="h-4 w-4" aria-hidden="true" />
          {t('tickets.refresh')}
        </button>
        <TicketList tickets={tickets} selectedId={selectedId} onSelect={setSelectedId} />
      </div>
      <TicketDetailPage
        detail={detail}
        fallback={
          created
            ? {
                ticket: created.ticket,
                events: created.events,
                pending_actions: created.pending_actions,
                citations: created.citations
              }
            : null
        }
      />
    </div>
  );
}

export default TicketsPage;
