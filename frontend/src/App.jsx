import { useState } from 'react';
import { useDebateSocket } from './useDebateSocket';
import { cx } from './lib/cx';
import DebateHeader from './components/DebateHeader';
import SetupPanel from './components/SetupPanel';
import SideColumn from './components/SideColumn';
import ConflictReview from './components/ConflictReview';
import FinalAdjudication from './components/FinalAdjudication';
import ConnectionBanner from './components/ConnectionBanner';

// Turns the active speaker signal into per-side live status text.
function sideStatus(activeSpeaker, side) {
  const map = {
    PRO: { PRO: 'Composing argument' },
    PRO_AUDITING: { PRO: 'Argument under audit' },
    PRO_REVISING: { PRO: 'Revising argument' },
    CON: { CON: 'Composing argument' },
    CON_AUDITING: { CON: 'Argument under audit' },
    CON_REVISING: { CON: 'Revising argument' },
  };
  return map[activeSpeaker]?.[side] || null;
}

export default function App() {
  const {
    topic,
    maxRounds,
    status,
    phase,
    connectionState,
    errorMessage,
    activeSpeaker,
    currentRound,
    proTurns,
    conTurns,
    clashes,
    adjudication,
    startDebate,
    reconnect,
    reset,
  } = useDebateSocket();

  // Mobile: which side is shown (desktop shows both).
  const [mobileSide, setMobileSide] = useState('PRO');

  const isIdle = status === 'IDLE';
  const proActive = ['PRO', 'PRO_AUDITING', 'PRO_REVISING'].includes(activeSpeaker);
  const conActive = ['CON', 'CON_AUDITING', 'CON_REVISING'].includes(activeSpeaker);

  if (isIdle) {
    return (
      <main className="min-h-screen">
        <SetupPanel onStart={startDebate} disabled={status === 'STARTING'} />
      </main>
    );
  }

  const resolving = activeSpeaker === 'RESOLVING_CLASH';

  return (
    <div className="min-h-screen">
      <DebateHeader
        topic={topic}
        phase={phase}
        currentRound={currentRound}
        maxRounds={maxRounds}
        onReset={reset}
      />

      <ConnectionBanner
        connectionState={connectionState}
        status={status}
        errorMessage={errorMessage}
        onReconnect={reconnect}
      />

      <main className="mx-auto max-w-6xl px-4 pb-24 pt-6 sm:px-6">
        {status === 'RESEARCHING' && (
          <div className="mb-6 flex items-center justify-center gap-2.5 rounded border border-line bg-surface py-4 text-[13px] text-muted">
            <span className="draft-dot inline-block h-2 w-2 rounded-full bg-pro" />
            Researching the motion — gathering and grounding evidence before opening statements.
          </div>
        )}

        {/* Mobile side switcher */}
        <div className="mb-4 grid grid-cols-2 gap-1.5 md:hidden">
          {['PRO', 'CON'].map((s) => {
            const isPro = s === 'PRO';
            const active = mobileSide === s;
            return (
              <button
                key={s}
                type="button"
                onClick={() => setMobileSide(s)}
                className={cx(
                  'rounded border py-2 text-[12px] font-semibold transition-colors',
                  active && isPro && 'border-pro bg-pro-soft text-pro-ink',
                  active && !isPro && 'border-con bg-con-soft text-con-ink',
                  !active && 'border-line text-muted'
                )}
              >
                {isPro ? 'Affirmative' : 'Opposition'}
                <span className="tnum ml-1 text-faint">
                  ({isPro ? proTurns.length : conTurns.length})
                </span>
              </button>
            );
          })}
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 md:gap-8">
          <div className={cx(mobileSide === 'PRO' ? 'block' : 'hidden', 'md:block')}>
            <SideColumn
              side="PRO"
              turns={proTurns}
              isActive={proActive}
              statusText={sideStatus(activeSpeaker, 'PRO')}
            />
          </div>
          <div className={cx(mobileSide === 'CON' ? 'block' : 'hidden', 'md:block')}>
            <SideColumn
              side="CON"
              turns={conTurns}
              isActive={conActive}
              statusText={sideStatus(activeSpeaker, 'CON')}
            />
          </div>
        </div>

        {(clashes.length > 0 || resolving) && (
          <section className="mt-10" aria-label="Conflict resolution">
            <div className="mb-4 flex items-center gap-3">
              <h2 className="font-serif text-lg font-semibold text-ink">Conflict resolution</h2>
              <span className="h-px flex-1 bg-line" aria-hidden="true" />
              <span className="text-[11.5px] text-faint">Referee · evidence-grounded rulings</span>
            </div>
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              {clashes.map((clash, i) => (
                <ConflictReview key={clash.resolution_id || i} clash={clash} index={i} />
              ))}
              {resolving && (
                <div className="flex items-center gap-2.5 rounded border border-dashed border-line-strong bg-surface p-4 text-[13px] text-muted">
                  <span className="draft-dot inline-block h-2 w-2 rounded-full bg-caution" />
                  Reconciling conflicting claims against the evidence record…
                </div>
              )}
            </div>
          </section>
        )}

        {adjudication && (
          <section className="mt-10" aria-label="Final adjudication">
            <FinalAdjudication adjudication={adjudication} />
          </section>
        )}
      </main>
    </div>
  );
}
