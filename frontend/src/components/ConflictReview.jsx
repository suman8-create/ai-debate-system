import { cx } from '../lib/cx';
import { Tag, Overline } from './ui';
import { favoredLabel } from '../lib/debate';

function favorTone(side) {
  const v = String(side || '').toUpperCase();
  if (v === 'PRO') return 'pro';
  if (v === 'CON') return 'con';
  if (v === 'BOTH_VALID') return 'verified';
  return 'muted';
}

export default function ConflictReview({ clash, index }) {
  const hasConflict = clash.has_direct_conflict;

  return (
    <div className="rise-in rounded border border-line bg-surface p-4">
      <div className="flex items-center justify-between gap-3">
        <Overline>Clash review · Round {index + 1}</Overline>
        <Tag tone={hasConflict ? 'caution' : 'muted'}>
          {hasConflict ? 'Direct conflict' : 'No direct conflict'}
        </Tag>
      </div>

      {Array.isArray(clash.conflicting_claims) && clash.conflicting_claims.length > 0 && (
        <ul className="mt-3 space-y-1.5">
          {clash.conflicting_claims.map((c, i) => (
            <li key={i} className="flex gap-2 text-[13px] leading-relaxed text-ink-soft">
              <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-faint" aria-hidden="true" />
              <span>{c}</span>
            </li>
          ))}
        </ul>
      )}

      <div className="mt-3 rounded bg-verified-soft/50 p-3">
        <Overline className="text-verified">Empirical ground truth</Overline>
        <p className="mt-1 text-[13.5px] leading-relaxed text-ink-soft">
          {clash.empirical_ground_truth}
        </p>
      </div>

      {clash.resolution_notes && (
        <p className="mt-3 text-[13px] leading-relaxed text-muted">{clash.resolution_notes}</p>
      )}

      <div className="mt-3 flex items-center gap-2 border-t border-line pt-3">
        <span className="text-[11.5px] text-faint">Referee ruling</span>
        <Tag tone={favorTone(clash.favored_side)}>{favoredLabel(clash.favored_side)}</Tag>
      </div>
    </div>
  );
}
