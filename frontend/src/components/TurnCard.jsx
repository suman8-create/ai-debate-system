import { useState } from 'react';
import { cx } from '../lib/cx';
import { Tag, Overline, Meter } from './ui';
import {
  humanize,
  pct,
  verdictMeta,
  evidenceMeta,
  evidenceStatusMeta,
  realFallacies,
  sourceHost,
} from '../lib/debate';

function AuditDetail({ audit }) {
  const verdict = verdictMeta(audit.verdict);
  const evidence = evidenceMeta(audit.evidence_validity);
  const fallacies = realFallacies(audit.detected_fallacies);

  return (
    <div className="mt-3 border-t border-line pt-3">
      <div className="flex items-center justify-between gap-3">
        <Overline>Independent audit</Overline>
        <Tag tone={verdict.tone}>{verdict.label}</Tag>
      </div>

      <div className="mt-3 grid grid-cols-1 gap-x-6 gap-y-2.5 sm:grid-cols-3">
        <Meter label="Source quality" value={pct(audit.source_quality_score)} tone="ink" />
        <Meter label="Logical strength" value={pct(audit.logical_strength_score)} tone="ink" />
        <Meter label="Relevance" value={pct(audit.relevance_score)} tone="ink" />
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-1.5">
        <Tag tone={evidence.tone}>{evidence.label}</Tag>
        {fallacies.length > 0 ? (
          fallacies.map((f, i) => (
            <Tag key={i} tone="flagged">
              {humanize(f)}
            </Tag>
          ))
        ) : (
          <Tag tone="verified">No fallacies detected</Tag>
        )}
      </div>

      {audit.feedback_notes && (
        <p className="mt-3 border-l-2 border-line-strong pl-3 text-[13px] leading-relaxed text-muted">
          <span className="font-semibold text-ink-soft">Auditor note. </span>
          {audit.feedback_notes}
        </p>
      )}
    </div>
  );
}

function EvidenceDetail({ evidence }) {
  if (!evidence) return null;
  const status = evidenceStatusMeta(evidence.status);
  const host = sourceHost(evidence.source_url);

  return (
    <div className="mt-3 rounded bg-sunken/60 p-3">
      <div className="flex items-center justify-between gap-3">
        <Overline>Evidence</Overline>
        <Tag tone={status.tone}>{status.label}</Tag>
      </div>
      {evidence.quote && (
        <blockquote className="mt-2 font-serif text-[15px] italic leading-relaxed text-ink-soft">
          &ldquo;{evidence.quote}&rdquo;
        </blockquote>
      )}
      {evidence.claim_text && (
        <p className="mt-2 text-[13px] leading-relaxed text-muted">{evidence.claim_text}</p>
      )}
      <div className="mt-2.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[12px] text-faint">
        {evidence.publisher && <span className="font-medium text-muted">{evidence.publisher}</span>}
        {host &&
          (evidence.source_url ? (
            <a
              href={evidence.source_url}
              target="_blank"
              rel="noreferrer"
              className="underline decoration-line-strong underline-offset-2 hover:text-ink"
            >
              {host}
            </a>
          ) : (
            <span>{host}</span>
          ))}
        {evidence.evidence_score != null && (
          <span className="tnum">grounding {pct(evidence.evidence_score)}%</span>
        )}
      </div>
    </div>
  );
}

export default function TurnCard({ turn, side }) {
  const [open, setOpen] = useState(false);
  const { argument, audit, revisionRequired, history = [] } = turn;
  const isPro = side === 'PRO';
  const accent = isPro ? 'pro' : 'con';

  const typeLabel = humanize(argument.argument_type);
  const auditing = !audit && !revisionRequired;

  return (
    <article
      className={cx(
        'rise-in rounded border bg-surface',
        isPro ? 'border-l-2 border-l-pro border-line' : 'border-l-2 border-l-con border-line'
      )}
    >
      <div className="p-4">
        <div className="flex items-center justify-between gap-2">
          <Overline className={isPro ? 'text-pro' : 'text-con'}>
            Round {argument.round_number} · {typeLabel}
          </Overline>
          {argument.target_claim_id && (
            <span className="tnum inline-flex items-center gap-1 rounded-full bg-sunken px-2 py-0.5 text-[10.5px] font-medium text-muted">
              rebuts {argument.target_claim_id}
            </span>
          )}
        </div>

        <h4 className="mt-2 text-balance font-serif text-[19px] font-medium leading-snug text-ink">
          {argument.claim}
        </h4>

        <div className="mt-3 flex flex-wrap items-center gap-1.5">
          {history.length > 0 && (
            <Tag tone="muted">
              Revised{history.length > 1 ? ` ×${history.length}` : ''}
            </Tag>
          )}
          {auditing && (
            <Tag tone={accent}>
              <span className="draft-dot inline-block h-1.5 w-1.5 rounded-full bg-current" />
              Under audit
            </Tag>
          )}
          {revisionRequired && !audit && <Tag tone="caution">Revising</Tag>}
          {audit && <Tag tone={verdictMeta(audit.verdict).tone}>{verdictMeta(audit.verdict).label}</Tag>}
        </div>

        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          className="mt-3 inline-flex items-center gap-1 text-[12px] font-semibold text-muted transition-colors hover:text-ink"
        >
          {open ? 'Hide reasoning & evidence' : 'Reasoning, impact & evidence'}
          <span aria-hidden="true" className={cx('transition-transform', open && 'rotate-90')}>
            ›
          </span>
        </button>

        {open && (
          <div className="mt-3 space-y-3 border-t border-line pt-3">
            <div>
              <Overline>Reasoning</Overline>
              <p className="mt-1 text-[14px] leading-relaxed text-ink-soft">{argument.reasoning}</p>
            </div>
            <div>
              <Overline>Impact</Overline>
              <p className="mt-1 text-[14px] leading-relaxed text-ink-soft">{argument.impact}</p>
            </div>
            <EvidenceDetail evidence={argument.evidence} />
            {argument.source_citation && !argument.evidence && (
              <p className="text-[12px] text-faint">
                Source:{' '}
                <span className="text-muted">{sourceHost(argument.source_citation) || argument.source_citation}</span>
              </p>
            )}
          </div>
        )}

        {audit && <AuditDetail audit={audit} />}

        {history.length > 0 && (
          <details className="mt-3 border-t border-line pt-3">
            <summary className="cursor-pointer text-[12px] font-semibold text-muted hover:text-ink">
              Superseded version{history.length > 1 ? 's' : ''} ({history.length})
            </summary>
            <div className="mt-2 space-y-2">
              {history.map((h, i) => (
                <div key={i} className="rounded border border-dashed border-line-strong p-2.5">
                  <p className="font-serif text-[14px] italic leading-snug text-muted line-through decoration-line-strong">
                    {h.argument.claim}
                  </p>
                  {h.audit?.feedback_notes && (
                    <p className="mt-1.5 text-[12px] leading-relaxed text-faint">
                      {h.audit.feedback_notes}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </details>
        )}
      </div>
    </article>
  );
}
