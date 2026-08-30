import { cx } from '../lib/cx';

const TONE_CLASSES = {
  verified: 'bg-verified-soft text-verified border-verified/25',
  flagged: 'bg-flagged-soft text-flagged border-flagged/25',
  caution: 'bg-caution-soft text-caution border-caution/30',
  pro: 'bg-pro-soft text-pro-ink border-pro-line',
  con: 'bg-con-soft text-con-ink border-con-line',
  muted: 'bg-sunken text-muted border-line-strong',
  ink: 'bg-ink text-paper border-ink',
};

export function Tag({ tone = 'muted', children, className }) {
  return (
    <span
      className={cx(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-medium leading-5 tracking-wide',
        TONE_CLASSES[tone] || TONE_CLASSES.muted,
        className
      )}
    >
      {children}
    </span>
  );
}

export function Dot({ tone = 'muted', pulse = false }) {
  const color = {
    verified: 'bg-verified',
    flagged: 'bg-flagged',
    caution: 'bg-caution',
    pro: 'bg-pro',
    con: 'bg-con',
    muted: 'bg-faint',
  }[tone];
  return (
    <span
      className={cx('inline-block h-1.5 w-1.5 shrink-0 rounded-full', color, pulse && 'draft-dot')}
      aria-hidden="true"
    />
  );
}

// Overline / eyebrow label — small, tracked, uppercase metadata.
export function Overline({ children, className }) {
  return (
    <span
      className={cx(
        'block text-[10.5px] font-semibold uppercase tracking-[0.16em] text-faint',
        className
      )}
    >
      {children}
    </span>
  );
}

// Horizontal meter for a normalised 0–100 metric.
export function Meter({ value, tone = 'pro', label, unit = '%' }) {
  const pctValue = Math.max(0, Math.min(100, value ?? 0));
  const barColor = {
    pro: 'bg-pro',
    con: 'bg-con',
    verified: 'bg-verified',
    flagged: 'bg-flagged',
    caution: 'bg-caution',
    ink: 'bg-ink',
  }[tone];

  return (
    <div>
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-xs text-muted">{label}</span>
        <span className="tnum text-xs font-semibold text-ink-soft">
          {value ?? '—'}
          {value != null ? unit : ''}
        </span>
      </div>
      <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-sunken">
        <div
          className={cx('h-full rounded-full transition-[width] duration-700 ease-out', barColor)}
          style={{ width: `${pctValue}%` }}
        />
      </div>
    </div>
  );
}
