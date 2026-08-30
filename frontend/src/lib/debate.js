// Presentation helpers for the debate UI. No backend contracts here — only
// formatting and labelling of values the backend already emits.

export const PRESET_TOPICS = [
  'Should artificial intelligence development be paused?',
  'Is a universal basic income economically viable?',
  'Should social media platforms be regulated as publishers?',
  'Should college education be tuition-free?',
  'Does remote work improve long-term productivity?',
];

export const DEBATE_FORMATS = [
  { value: 'STANDARD', label: 'Standard', hint: 'Constructive → rebuttal → closing' },
  { value: 'RAPID', label: 'Rapid', hint: 'Condensed single-exchange rounds' },
  { value: 'CROSS_EXAM', label: 'Cross-examination', hint: 'Direct claim-by-claim clash' },
];

// Maps the live phase to a short editorial label + one-line description.
export function phaseLabel(phase) {
  switch (phase) {
    case 'RESEARCH':
      return { label: 'Research', detail: 'Gathering and indexing evidence' };
    case 'PRO_DRAFTING':
      return { label: 'Drafting', detail: 'Affirmative composing its argument' };
    case 'PRO_AUDIT':
      return { label: 'Audit', detail: 'Verifying the affirmative argument' };
    case 'CON_DRAFTING':
      return { label: 'Drafting', detail: 'Opposition composing its argument' };
    case 'CON_AUDIT':
      return { label: 'Audit', detail: 'Verifying the opposition argument' };
    case 'CONFLICT':
      return { label: 'Conflict review', detail: 'Reconciling claims against evidence' };
    case 'COMPLETE':
      return { label: 'Adjudicated', detail: 'Final verdict delivered' };
    default:
      return { label: 'Standby', detail: 'Awaiting debate start' };
  }
}

// Score helpers — backend audit scores are normalised 0.0–1.0.
export function pct(score) {
  if (score === null || score === undefined || Number.isNaN(Number(score))) return null;
  return Math.round(Number(score) * 100);
}

// Judge scorecards are already 0–100.
export function roundScore(score) {
  if (score === null || score === undefined || Number.isNaN(Number(score))) return 0;
  return Math.round(Number(score));
}

export function verdictMeta(verdict) {
  const v = String(verdict || '').toUpperCase();
  if (v === 'PASS') return { label: 'Verified', tone: 'verified' };
  if (v === 'REVISE') return { label: 'Revision required', tone: 'caution' };
  if (v === 'FORFEIT') return { label: 'Forfeited', tone: 'flagged' };
  return { label: v || 'Pending', tone: 'muted' };
}

export function evidenceMeta(validity) {
  const v = String(validity || '').toUpperCase();
  if (v === 'SUPPORTED') return { label: 'Evidence supported', tone: 'verified' };
  if (v === 'CONTRADICTED') return { label: 'Evidence contradicted', tone: 'flagged' };
  if (v === 'HALLUCINATED') return { label: 'Evidence unfounded', tone: 'flagged' };
  if (v === 'UNSUPPORTED') return { label: 'Evidence unsupported', tone: 'caution' };
  if (v === 'UNVERIFIED') return { label: 'Evidence unverified', tone: 'caution' };
  return { label: humanize(v), tone: 'muted' };
}

// EvidenceUnit.status is SUPPORTED / CONTRADICTED / UNVERIFIED.
export function evidenceStatusMeta(status) {
  const v = String(status || '').toUpperCase();
  if (v === 'SUPPORTED') return { label: 'Supported', tone: 'verified' };
  if (v === 'CONTRADICTED') return { label: 'Contradicted', tone: 'flagged' };
  return { label: 'Unverified', tone: 'caution' };
}

// Pull a readable host from a URL for compact source display.
export function sourceHost(url) {
  if (!url) return null;
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return String(url).replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0];
  }
}

export function humanize(value) {
  if (!value) return '';
  return String(value)
    .toLowerCase()
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

export function realFallacies(list) {
  if (!Array.isArray(list)) return [];
  return list.filter((f) => String(f).toUpperCase() !== 'NO_FALLACY');
}

export function favoredLabel(side) {
  const v = String(side || '').toUpperCase();
  if (v === 'PRO') return 'Affirmative interpretation favoured';
  if (v === 'CON') return 'Opposition interpretation favoured';
  if (v === 'BOTH_VALID') return 'Both readings hold';
  return 'No side favoured';
}
