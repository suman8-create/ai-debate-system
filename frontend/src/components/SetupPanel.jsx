import { useState } from 'react';
import { cx } from '../lib/cx';
import { Overline } from './ui';
import { PRESET_TOPICS, DEBATE_FORMATS } from '../lib/debate';

export default function SetupPanel({ onStart, disabled }) {
  const [topic, setTopic] = useState('');
  const [rounds, setRounds] = useState(2);
  const [format, setFormat] = useState('STANDARD');

  const canStart = topic.trim().length > 8 && !disabled;

  const submit = (e) => {
    e.preventDefault();
    if (!canStart) return;
    onStart(topic.trim(), rounds, format);
  };

  return (
    <div className="mx-auto max-w-2xl px-4 py-10 sm:py-16">
      <div className="text-center">
        <Overline className="text-pro">Evidence-based AI adjudication</Overline>
        <h1 className="mt-3 text-balance font-serif text-4xl font-semibold leading-[1.1] text-ink sm:text-5xl">
          Two agents. One motion.
          <br />
          <span className="text-muted">A verdict grounded in evidence.</span>
        </h1>
        <p className="mx-auto mt-4 max-w-lg text-pretty text-[15px] leading-relaxed text-muted">
          Pose a motion and watch an affirmative and opposition agent argue in real time — every
          claim researched, independently audited for fallacies, and formally adjudicated.
        </p>
      </div>

      <form
        onSubmit={submit}
        className="mt-8 rounded-lg border border-line bg-surface p-5 sm:p-6"
      >
        <label htmlFor="topic" className="block">
          <Overline>The motion</Overline>
          <textarea
            id="topic"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            rows={2}
            placeholder="e.g. Should artificial intelligence development be paused?"
            className="mt-2 w-full resize-none rounded border border-line-strong bg-paper px-3.5 py-3 font-serif text-[17px] leading-snug text-ink placeholder:text-faint focus:border-pro focus:bg-surface"
          />
        </label>

        <div className="mt-2 flex flex-wrap gap-1.5">
          {PRESET_TOPICS.map((preset) => (
            <button
              key={preset}
              type="button"
              onClick={() => setTopic(preset)}
              className="rounded-full border border-line px-2.5 py-1 text-left text-[11.5px] text-muted transition-colors hover:border-pro hover:text-pro"
            >
              {preset}
            </button>
          ))}
        </div>

        <div className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2">
          <div>
            <Overline>Rounds</Overline>
            <div className="mt-2 flex gap-1.5">
              {[1, 2, 3].map((n) => (
                <button
                  key={n}
                  type="button"
                  onClick={() => setRounds(n)}
                  className={cx(
                    'tnum h-10 flex-1 rounded border text-[14px] font-semibold transition-colors',
                    rounds === n
                      ? 'border-ink bg-ink text-paper'
                      : 'border-line-strong text-muted hover:border-ink hover:text-ink'
                  )}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>

          <div>
            <Overline>Format</Overline>
            <div className="mt-2 flex gap-1.5">
              {DEBATE_FORMATS.map((f) => (
                <button
                  key={f.value}
                  type="button"
                  onClick={() => setFormat(f.value)}
                  title={f.hint}
                  className={cx(
                    'h-10 flex-1 rounded border px-1 text-[11.5px] font-semibold leading-tight transition-colors',
                    format === f.value
                      ? 'border-ink bg-ink text-paper'
                      : 'border-line-strong text-muted hover:border-ink hover:text-ink'
                  )}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <button
          type="submit"
          disabled={!canStart}
          className={cx(
            'mt-6 h-12 w-full rounded font-semibold transition-colors',
            canStart
              ? 'bg-pro text-white hover:bg-pro-ink'
              : 'cursor-not-allowed bg-sunken text-faint'
          )}
        >
          {disabled ? 'Convening debate…' : 'Open the floor'}
        </button>
        <p className="mt-2 text-center text-[11.5px] text-faint">
          Requires the debate engine running at 127.0.0.1:8000
        </p>
      </form>
    </div>
  );
}
