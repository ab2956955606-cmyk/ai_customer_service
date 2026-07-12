import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { useI18n } from '../i18n';

type ChartDatum = { name: string; value: number };

type Props = {
  categories: ChartDatum[];
  priorities: ChartDatum[];
};

const palette = ['#0f766e', '#b45309', '#be123c', '#2563eb', '#475569', '#16a34a'];

function Charts({ categories, priorities }: Props) {
  const { t, label } = useI18n();
  const localizedCategories = categories.map((item) => ({ ...item, name: label(item.name) }));
  const localizedPriorities = priorities.map((item) => ({ ...item, name: label(item.name) }));
  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <section className="panel p-4">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-ink">{t('dashboard.categoryMix')}</h2>
        </div>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={localizedCategories}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="value" fill="#0f766e" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="panel p-4">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-ink">{t('dashboard.priorityMix')}</h2>
        </div>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={localizedPriorities} dataKey="value" nameKey="name" outerRadius={90} label>
                {localizedPriorities.map((_, index) => (
                  <Cell key={index} fill={palette[index % palette.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  );
}

export default Charts;
