import { FormEvent, useState } from 'react';
import { Send } from 'lucide-react';
import { api, TicketWorkflowResponse } from '../api/client';
import { useI18n } from '../i18n';

type Props = {
  onCreated: (response: TicketWorkflowResponse) => void;
  deepSeekApiKey: string | null;
};

function TicketForm({ onCreated, deepSeekApiKey }: Props) {
  const { t } = useI18n();
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [customerEmail, setCustomerEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await api.createTicket(
        {
          subject,
          description,
          customer_email: customerEmail || undefined
        },
        deepSeekApiKey
      );
      onCreated(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('ticket.submitFailed'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={submit} className="panel p-4">
      <div className="grid gap-3">
        <label className="grid gap-1 text-sm font-medium text-slate-700">
          {t('ticket.subject')}
          <input className="input" value={subject} onChange={(event) => setSubject(event.target.value)} placeholder={t('ticket.subjectPlaceholder')} required />
        </label>
        <label className="grid gap-1 text-sm font-medium text-slate-700">
          {t('ticket.customerEmail')}
          <input className="input" type="email" value={customerEmail} onChange={(event) => setCustomerEmail(event.target.value)} placeholder={t('ticket.emailPlaceholder')} />
        </label>
        <label className="grid gap-1 text-sm font-medium text-slate-700">
          {t('ticket.description')}
          <textarea className="input min-h-32 resize-y" value={description} onChange={(event) => setDescription(event.target.value)} placeholder={t('ticket.descriptionPlaceholder')} required />
        </label>
        {error && <p className="text-sm text-rosewood">{error}</p>}
        <button type="submit" className="btn btn-primary w-full" disabled={loading}>
          <Send className="h-4 w-4" aria-hidden="true" />
          {loading ? t('ticket.submitting') : t('ticket.submit')}
        </button>
      </div>
    </form>
  );
}

export default TicketForm;
