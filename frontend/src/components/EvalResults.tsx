import { EvalPayload } from '../api/client';
import { useI18n } from '../i18n';

type Props = {
  payload: EvalPayload | null;
};

function EvalResults({ payload }: Props) {
  const { t, label } = useI18n();
  const metrics = payload?.metrics ?? {};
  const audit = payload?.llm_execution;
  const metricLabels: Record<string, string> = {
    routing_accuracy: t('evals.routing'),
    escalation_accuracy: t('evals.escalation'),
    unsafe_action_block_rate: t('evals.unsafeBlock'),
    approval_gate_accuracy: t('evals.approvalGate'),
    citation_presence_rate: t('evals.citations'),
    response_language_accuracy: t('evals.responseLanguage'),
    average_latency_ms: t('evals.averageLatency')
  };
  return (
    <div className="grid gap-4">
      {audit && (
        <section className="panel flex flex-wrap items-center justify-between gap-3 p-4">
          <div>
            <h2 className="text-sm font-semibold text-ink">{t('evals.llmExecution')}</h2>
            <p className="mt-1 text-xs text-slate-500">
              {t('evals.provider')}: {audit.provider} · {audit.model} · {t('evals.datasetLanguage')}: {payload?.locale === 'zh' ? t('evals.languageZh') : t('evals.languageEn')}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className="badge border-slate-200 bg-slate-50 text-slate-600">{t('evals.calls')} {audit.attempted_calls}</span>
            <span className="badge border-teal-200 bg-teal-50 text-ocean">{t('evals.successfulCalls')} {audit.successful_calls}</span>
            <span className="badge border-rose-200 bg-rose-50 text-rosewood">{t('evals.failedCalls')} {audit.failed_calls}</span>
            <span className="badge border-amber-200 bg-amber-50 text-ember">{t('evals.fallbackCalls')} {audit.fallback_calls}</span>
            <span className="badge border-slate-200 bg-slate-50 text-slate-600">{t('evals.retries')} {audit.retry_attempts}</span>
          </div>
        </section>
      )}
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-7">
        {Object.entries(metrics).map(([key, value]) => (
          <section key={key} className="panel p-4">
            <p className="text-xs font-medium uppercase text-slate-500">{metricLabels[key] ?? key}</p>
            <p className="mt-2 text-2xl font-semibold text-ink">{key.includes('latency') ? `${value} ms` : value}</p>
          </section>
        ))}
      </div>

      <section className="panel overflow-hidden">
        <div className="border-b border-slate-200 p-4">
          <h2 className="text-sm font-semibold text-ink">{t('evals.results')}</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">{t('evals.case')}</th>
                <th className="px-4 py-3">{t('evals.route')}</th>
                <th className="px-4 py-3">{t('evals.category')}</th>
                <th className="px-4 py-3">{t('evals.priority')}</th>
                <th className="px-4 py-3">{t('evals.llm')}</th>
                <th className="px-4 py-3">{t('evals.responseLanguage')}</th>
                <th className="px-4 py-3">{t('common.latency')}</th>
                <th className="px-4 py-3">{t('evals.status')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {(payload?.results ?? []).map((result) => (
                <tr key={result.id}>
                  <td className="px-4 py-3 font-medium text-ink">{result.id}</td>
                  <td className="px-4 py-3 text-slate-600">{label(result.actual_route)}</td>
                  <td className="px-4 py-3 text-slate-600">{label(result.actual_category)}</td>
                  <td className="px-4 py-3 text-slate-600">{label(result.actual_priority)}</td>
                  <td className="px-4 py-3 text-slate-600">
                    {result.llm_calls ? `${result.llm_calls.successful_calls}/${result.llm_calls.attempted_calls}` : '-'}
                  </td>
                  <td className="px-4 py-3 text-slate-600">{label(result.response_language_ok ? 'passed' : 'failed')}</td>
                  <td className="px-4 py-3 text-slate-600">{result.latency_ms} ms</td>
                  <td className="px-4 py-3">
                    <span className={`badge ${result.passed ? 'border-teal-200 bg-teal-50 text-ocean' : 'border-rose-200 bg-rose-50 text-rosewood'}`}>
                      {label(result.passed ? 'passed' : 'failed')}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

export default EvalResults;
