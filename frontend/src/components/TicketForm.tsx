import { FormEvent, useState } from 'react';
import { Send } from 'lucide-react';
import { api, TicketWorkflowResponse } from '../api/client';

type Props = {
  onCreated: (response: TicketWorkflowResponse) => void;
};

function TicketForm({ onCreated }: Props) {
  const [subject, setSubject] = useState('Cannot reset password');
  const [description, setDescription] = useState('The reset link is not arriving in my email.');
  const [customerEmail, setCustomerEmail] = useState('alice@example.com');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await api.createTicket({
        subject,
        description,
        customer_email: customerEmail || undefined
      });
      onCreated(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ticket submission failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={submit} className="panel p-4">
      <div className="grid gap-3">
        <label className="grid gap-1 text-sm font-medium text-slate-700">
          Subject
          <input className="input" value={subject} onChange={(event) => setSubject(event.target.value)} />
        </label>
        <label className="grid gap-1 text-sm font-medium text-slate-700">
          Customer email
          <input className="input" value={customerEmail} onChange={(event) => setCustomerEmail(event.target.value)} />
        </label>
        <label className="grid gap-1 text-sm font-medium text-slate-700">
          Description
          <textarea className="input min-h-32 resize-y" value={description} onChange={(event) => setDescription(event.target.value)} />
        </label>
        {error && <p className="text-sm text-rosewood">{error}</p>}
        <button type="submit" className="btn btn-primary w-full" disabled={loading}>
          <Send className="h-4 w-4" aria-hidden="true" />
          {loading ? 'Submitting' : 'Submit ticket'}
        </button>
      </div>
    </form>
  );
}

export default TicketForm;
