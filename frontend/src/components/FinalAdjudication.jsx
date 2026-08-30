import { cx } from '../lib/cx';
import { Overline } from './ui';
import { roundScore } from '../lib/debate';

const CRITERIA = [
  { key: 'argumentation_strength', label: 'Argumentation', max: 30 },
  { key: 'evidence_quality', label: 'Evidence quality', max: 25 },
  { key: 'rebuttal_effectiveness', label: 'Rebuttal', max: 25 },
  { key: 'persuasion_and_impact', label: 'Persuasion & impact', max: 20 },
];

function ScoreRow({ label, max, pro, con }) {
  const proVal = roundScore(pro);
  const conVal = roundScore(con);
  const proWins = proVal > conVal;
  const conWins = conVal > proVal;
  return (
    <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 py-2.5">
      <div className="flex items-center justify-end gap-2">
        <div className="h-1.5 w-full max-w-[120px] overflow-hidden rounded-full bg-sunken">
          <div
            className="ml-auto h-full rounded-full bg-pro"
            style={{ width: `${(proVal / max) * 100}%` }}
          />
        </div>
        <span className={cx('tnum w-7 text-right text-[13px] font-semibold', proWins ? 'text-pro' : 'text-muted')}>
          {proVal}
        </span>
      </div>
      <div className="min-w-0 text-center">
        <span className="text-[11px] uppercase tracking-wide text-faint">{label}</span>
        <span className="tnum block text-[10px] text-faint">/ {max}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className={cx('tnum w-7 text-[13px] font-semibold', conWins ? 'text-con' : 'text-muted')}>
          {conVal}
        </span>
        <div className="h-1.5 w-full max-w-[120px] overflow-hidden rounded-full bg-sunken">
          <div className="h-full rounded-full bg-con" style={{ width: `${(conVal / max) * 100}%` }} />
        </div>
      </div>
    </div>
  );
}

function ClashList({ title, items, tone }) {
  if (!items || items.length === 0) return null;
  return (
    <div>
      <Overline className={tone === 'pro' ? 'text-pro' : 'text-con'}>{title}</Overline>
      <ul className="mt-2 space-y-1.5">
        {items.map((c, i) => (
          <li key={i} className="flex gap-2 text-[13px] leading-relaxed text-ink-soft">
            <span
              className={cx('mt-1.5 h-1 w-1 shrink-0 rounded-full', tone === 'pro' ? 'bg-pro' : 'bg-con')}
              aria-hidden="true"
            />
            <span>{c}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function FinalAdjudication({ adjudication }) {
  const verdict = adjudication?.judge_verdict || {};
  const pro = verdict.pro_scorecard || {};
  const con = verdict.con_scorecard || {};
  const winner = String(adjudication?.winner || verdict.winner || 'TIE').toUpperCase();

  const winnerLabel =
    winner === 'PRO' ? 'Affirmative' : winner === 'CON' ? 'Opposition' : 'Draw';
  const winnerTone = winner === 'PRO' ? 'text-pro' : winner === 'CON' ? 'text-con' : 'text-ink';

  const proTotal = roundScore(pro.total_score);
  const conTotal = roundScore(con.total_score);

  return (
    <section className="rise-in overflow-hidden rounded-lg border border-line-strong bg-surface">
      <div className="border-b border-line bg-sunken/50 px-6 py-5 text-center">
        <Overline className="text-faint">Final adjudication</Overline>
        <p className="mt-2 text-[13px] text-muted">
          {winner === 'TIE' ? 'The debate is judged a' : 'This debate is awarded to the'}
        </p>
        <h2 className={cx('mt-1 font-serif text-3xl font-semibold', winnerTone)}>{winnerLabel}</h2>
        <div className="mt-3 flex items-center justify-center gap-4">
          <span className="tnum text-[15px]">
            <span className={cx('font-semibold', winner === 'PRO' ? 'text-pro' : 'text-muted')}>
              {proTotal}
            </span>
            <span className="text-faint"> Pro</span>
          </span>
          <span className="text-faint" aria-hidden="true">
            ·
          </span>
          <span className="tnum text-[15px]">
            <span className={cx('font-semibold', winner === 'CON' ? 'text-con' : 'text-muted')}>
              {conTotal}
            </span>
            <span className="text-faint"> Con</span>
          </span>
        </div>
      </div>

      <div className="px-6 py-5">
        <div className="mb-1 flex items-center justify-between text-[11px] uppercase tracking-wide">
          <span className="text-pro">Affirmative</span>
          <span className="text-con">Opposition</span>
        </div>
        <div className="divide-y divide-line">
          {CRITERIA.map((c) => (
            <ScoreRow
              key={c.key}
              label={c.label}
              max={c.max}
              pro={pro[c.key]}
              con={con[c.key]}
            />
          ))}
        </div>
      </div>

      {(verdict.key_clashes_won_by_pro?.length > 0 ||
        verdict.key_clashes_won_by_con?.length > 0) && (
        <div className="grid grid-cols-1 gap-5 border-t border-line px-6 py-5 sm:grid-cols-2">
          <ClashList title="Clashes won by Pro" items={verdict.key_clashes_won_by_pro} tone="pro" />
          <ClashList title="Clashes won by Con" items={verdict.key_clashes_won_by_con} tone="con" />
        </div>
      )}

      {verdict.adjudication_rationale && (
        <div className="border-t border-line px-6 py-5">
          <Overline>Rationale</Overline>
          <p className="mt-2 whitespace-pre-line text-[14px] leading-relaxed text-ink-soft">
            {verdict.adjudication_rationale}
          </p>
        </div>
      )}
    </section>
  );
}
