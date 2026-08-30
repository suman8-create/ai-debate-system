import { cx } from '../lib/cx';
import { phaseLabel } from '../lib/debate';

const STEPS = [
  { key: 'RESEARCH', label: 'Research' },
  { key: 'PRO', label: 'Affirmative' },
  { key: 'CON', label: 'Opposition' },
  { key: 'CONFLICT', label: 'Clash' },
  { key: 'COMPLETE', label: 'Verdict' },
];

function stepGroup(phase) {
  if (phase === 'RESEARCH') return 'RESEARCH';
  if (phase === 'PRO_DRAFTING' || phase === 'PRO_AUDIT') return 'PRO';
  if (phase === 'CON_DRAFTING' || phase === 'CON_AUDIT') return 'CON';
  if (phase === 'CONFLICT') return 'CONFLICT';
  if (phase === 'COMPLETE') return 'COMPLETE';
  return null;
}

export default function DebateHeader({ topic, phase, currentRound, maxRounds, onReset }) {
  const { label, detail } = phaseLabel(phase);
  const activeGroup = stepGroup(phase);
  const activeIndex = STEPS.findIndex((s) => s.key === activeGroup);

  return (
    <header className="border-b border-line bg-surface/80 backdrop-blur">
      <div className="mx-auto max-w-6xl px-4 py-4 sm:px-6">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-faint">
              <span className="flex h-4 w-4 items-center justify-center rounded-sm border border-line-strong font-serif text-[10px] text-ink">
                D
              </span>
              Debate Arena
              <span className="text-line-strong" aria-hidden="true">
                /
              </span>
              <span className="tnum">
                Round {Math.min(currentRound, maxRounds)} of {maxRounds}
              </span>
            </div>
            <h1 className="mt-1.5 text-balance font-serif text-xl font-semibold leading-tight text-ink sm:text-2xl">
              {topic}
            </h1>
          </div>
          <button
            type="button"
            onClick={onReset}
            className="shrink-0 rounded border border-line-strong px-3 py-1.5 text-[12px] font-semibold text-muted transition-colors hover:border-ink hover:text-ink"
          >
            New debate
          </button>
        </div>

        <div className="mt-4 flex items-center gap-1.5 overflow-x-auto pb-1">
          {STEPS.map((step, i) => {
            const done = activeIndex > i;
            const active = activeIndex === i;
            return (
              <div key={step.key} className="flex items-center gap-1.5">
                <div
                  className={cx(
                    'flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium transition-colors',
                    active && 'border-ink bg-ink text-paper',
                    done && 'border-line-strong bg-sunken text-muted',
                    !active && !done && 'border-line text-faint'
                  )}
                >
                  {active && (
                    <span className="draft-dot inline-block h-1.5 w-1.5 rounded-full bg-current" />
                  )}
                  {step.label}
                </div>
                {i < STEPS.length - 1 && (
                  <span
                    className={cx('h-px w-4 sm:w-6', done ? 'bg-line-strong' : 'bg-line')}
                    aria-hidden="true"
                  />
                )}
              </div>
            );
          })}
          {phase !== 'COMPLETE' && phase !== 'IDLE' && (
            <span className="ml-2 hidden shrink-0 text-[12px] text-muted sm:inline">{detail}</span>
          )}
        </div>
      </div>
    </header>
  );
}
