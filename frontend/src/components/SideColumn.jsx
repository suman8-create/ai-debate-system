import { cx } from '../lib/cx';
import { Dot } from './ui';
import TurnCard from './TurnCard';

export default function SideColumn({ side, turns, statusText, isActive }) {
  const isPro = side === 'PRO';
  const accentText = isPro ? 'text-pro' : 'text-con';
  const accentBg = isPro ? 'bg-pro-soft' : 'bg-con-soft';
  const label = isPro ? 'Affirmative' : 'Opposition';
  const role = isPro ? 'Argues for the motion' : 'Argues against the motion';

  return (
    <section className="flex min-w-0 flex-col" aria-label={`${label} side`}>
      <header
        className={cx(
          'sticky top-0 z-10 border-b bg-paper/90 pb-3 pt-1 backdrop-blur',
          isActive ? (isPro ? 'border-pro' : 'border-con') : 'border-line'
        )}
      >
        <div className="flex items-center gap-2.5">
          <span
            className={cx(
              'flex h-8 w-8 items-center justify-center rounded-full font-serif text-[15px] font-semibold',
              accentBg,
              accentText
            )}
            aria-hidden="true"
          >
            {isPro ? 'P' : 'C'}
          </span>
          <div className="min-w-0">
            <h3 className={cx('font-serif text-[17px] font-semibold leading-none', accentText)}>
              {label}
            </h3>
            <p className="mt-1 text-[11.5px] text-muted">{role}</p>
          </div>
        </div>

        <div className="mt-2.5 flex h-4 items-center gap-1.5 text-[11.5px]">
          {isActive && statusText ? (
            <>
              <Dot tone={isPro ? 'pro' : 'con'} pulse />
              <span className={cx('font-medium', accentText)}>{statusText}</span>
            </>
          ) : (
            <span className="text-faint">
              {turns.length} argument{turns.length === 1 ? '' : 's'} on record
            </span>
          )}
        </div>
      </header>

      <div className="mt-4 flex flex-col gap-4">
        {turns.length === 0 && !isActive && (
          <div className="rounded border border-dashed border-line-strong p-6 text-center text-[13px] text-faint">
            Awaiting first argument
          </div>
        )}
        {turns.map((turn, i) => (
          <TurnCard key={turn.argument.argument_id || i} turn={turn} side={side} />
        ))}
      </div>
    </section>
  );
}
