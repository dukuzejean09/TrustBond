type Props = { title: string; value: string | number; subtitle?: string };
export default function KpiCard({ title, value, subtitle }: Props) {
  return (
    <div className="kpi card">
      <div className="title">{title}</div>
      <div className="value">{value}</div>
      {subtitle && (
        <div className="small-muted" style={{ marginTop: 6 }}>
          {subtitle}
        </div>
      )}
    </div>
  );
}
