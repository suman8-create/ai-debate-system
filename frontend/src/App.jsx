import React, { useState } from 'react';
import { useDebateSocket } from './useDebateSocket';
import { 
  CheckCircle2, 
  AlertCircle, 
  ExternalLink, 
  ChevronRight, 
  Scale, 
  Sparkles,
  BookOpen,
  CornerDownRight,
  ShieldCheck,
  RefreshCw
} from 'lucide-react';

const PRESET_MOTIONS = [
  "Should artificial intelligence development be paused?",
  "Is a universal basic income economically viable?",
  "Should social media platforms be regulated as publishers?",
  "Should college education be tuition-free?",
  "Does remote work improve long-term productivity?"
];

export default function App() {
  const [motionInput, setMotionInput] = useState("Should college education be tuition-free?");
  const [roundsCount, setRoundsCount] = useState(2);
  const [expandedArgId, setExpandedArgId] = useState(null);

  const {
    sessionId,
    topic,
    status,
    activeSpeaker,
    currentRound,
    proArguments,
    conArguments,
    proAudits,
    conAudits,
    clashes,
    adjudication,
    startDebate
  } = useDebateSocket();

  const handleLaunchDebate = (e) => {
    e?.preventDefault();
    if (!motionInput.trim()) return;
    const validatedRounds = Math.min(Math.max(Number(roundsCount) || 1, 1), 8);
    startDebate(motionInput.trim(), validatedRounds);
  };

  const isDebateRunning = status === 'RESEARCHING' || status === 'DEBATING' || status === 'STARTING';

  return (
    <div className="min-h-screen bg-[#F9F8F5] text-[#1A1A1A] flex flex-col items-center justify-start p-4 sm:p-8 selection:bg-blue-100">
      
      {/* Top Meta Header */}
      <header className="w-full max-w-5xl flex flex-col sm:flex-row sm:items-center justify-between border-b border-[#E6E4DD] pb-4 mb-8 gap-4">
        <div>
          <span className="text-[10px] font-mono tracking-widest uppercase text-[#73726E] block mb-1">
            EVIDENCE-BASED AI ADJUDICATION
          </span>
          <div className="text-sm font-semibold tracking-tight text-[#1A1A1A] flex items-center gap-2">
            <Scale className="w-4 h-4 text-[#1E3A8A]" /> Autonomous Dialectical Debate Engine
          </div>
        </div>

        {/* Live Engine Status Pill */}
        <div className="flex items-center gap-2 text-xs font-mono bg-white border border-[#E6E4DD] px-3 py-1.5 rounded-md shadow-xs">
          <span className={`w-2 h-2 rounded-full ${
            status === 'COMPLETED' ? 'bg-emerald-600' :
            isDebateRunning ? 'bg-amber-500 animate-pulse' : 'bg-slate-400'
          }`} />
          <span className="text-[#52514D]">
            {status === 'IDLE' && 'Engine Standing By'}
            {status === 'STARTING' && 'Initializing Session...'}
            {status === 'RESEARCHING' && 'Researching & Ingesting Evidence...'}
            {status === 'DEBATING' && `Round ${currentRound} in progress`}
            {status === 'COMPLETED' && 'Adjudication Sealed'}
            {status === 'ERROR' && 'Engine Disconnected'}
          </span>
        </div>
      </header>

      {/* Hero Header Section */}
      <div className="w-full max-w-3xl text-center mb-8">
        <h1 className="text-4xl sm:text-5xl font-serif tracking-tight text-[#1A1A1A] leading-[1.15] mb-3">
          Two agents. One motion.<br />
          <span className="italic text-[#52514D]">A verdict grounded in evidence.</span>
        </h1>
        <p className="text-sm text-[#73726E] max-w-xl mx-auto leading-relaxed">
          Pose a motion and observe affirmative and opposition agents debate in real-time. Every claim is empirically researched, independently audited for fallacies, and formally adjudicated.
        </p>
      </div>

      {/* Debate Setup / Motion Form (Faithful to Academic Layout) */}
      <div className="w-full max-w-2xl bg-white border border-[#E6E4DD] rounded-xl shadow-xs p-6 mb-12">
        <form onSubmit={handleLaunchDebate} className="flex flex-col gap-5">
          <div>
            <label className="text-[11px] font-mono tracking-wider uppercase text-[#73726E] block mb-2 font-medium">
              THE MOTION
            </label>
            <textarea
              rows={3}
              value={motionInput}
              onChange={(e) => setMotionInput(e.target.value)}
              disabled={isDebateRunning}
              placeholder="e.g. Should artificial intelligence development be paused?"
              className="w-full bg-[#FAFAF8] border border-[#E6E4DD] rounded-lg p-3 text-base font-serif text-[#1A1A1A] placeholder:text-[#A8A7A1] placeholder:font-sans focus:outline-none focus:border-[#1E3A8A] focus:bg-white transition resize-none disabled:opacity-60"
            />
          </div>

          {/* Preset Motion Badges */}
          <div className="flex flex-wrap gap-1.5">
            {PRESET_MOTIONS.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setMotionInput(preset)}
                disabled={isDebateRunning}
                className="text-xs bg-[#F2F1EC] hover:bg-[#EBE9E1] text-[#52514D] hover:text-[#1A1A1A] border border-[#E6E4DD] px-3 py-1.5 rounded-full transition text-left cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {preset}
              </button>
            ))}
          </div>

          {/* Configuration Controls: Flexible Round Text Box */}
          <div className="pt-2 border-t border-[#F2F1EC] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <label className="text-[11px] font-mono tracking-wider uppercase text-[#73726E] font-medium">
                ROUNDS:
              </label>
              <input
                type="number"
                min={1}
                max={8}
                value={roundsCount}
                onChange={(e) => setRoundsCount(e.target.value)}
                disabled={isDebateRunning}
                className="w-20 bg-[#FAFAF8] border border-[#E6E4DD] rounded-md px-3 py-1.5 text-xs font-mono text-[#1A1A1A] focus:outline-none focus:border-[#1E3A8A] text-center disabled:opacity-60 font-medium"
              />
              <span className="text-[11px] text-[#A8A7A1] italic">(Max 8 rounds)</span>
            </div>

            <button
              type="submit"
              disabled={isDebateRunning}
              className="w-full sm:w-auto bg-[#1E3A8A] hover:bg-[#1E3A8A]/90 text-white font-medium text-sm px-8 py-2.5 rounded-lg transition shadow-xs flex items-center justify-center gap-2 disabled:opacity-60 cursor-pointer disabled:cursor-not-allowed"
            >
              {isDebateRunning ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" /> Adjudicating...
                </>
              ) : (
                "Open the floor"
              )}
            </button>
          </div>
        </form>

        <p className="text-[11px] text-center text-[#A8A7A1] font-mono mt-4">
          Requires the debate engine running at 127.0.0.1:8000
        </p>
      </div>

      {/* Active Chamber: PRO vs CON Podiums */}
      {(proArguments.length > 0 || conArguments.length > 0 || isDebateRunning) && (
        <div className="w-full max-w-5xl space-y-8 animate-fade-in">
          
          {/* Active Motion Banner */}
          <div className="bg-white border-l-4 border-l-[#1E3A8A] border border-[#E6E4DD] rounded-r-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2 shadow-xs">
            <div>
              <span className="text-[10px] font-mono text-[#73726E] uppercase">DEBATED MOTION</span>
              <h2 className="text-lg font-serif text-[#1A1A1A] font-semibold">"{topic || motionInput}"</h2>
            </div>
            <span className="text-xs font-mono text-[#52514D] bg-[#F2F1EC] px-2.5 py-1 rounded">
              Phase: {status === 'RESEARCHING' ? 'Ingestion' : `Round ${currentRound}`}
            </span>
          </div>

          {/* Dual Podiums Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
            
            {/* PRO Podium */}
            <div className="bg-white border border-[#E6E4DD] rounded-xl p-5 shadow-xs">
              <div className="flex items-center justify-between border-b border-[#E6E4DD] pb-3 mb-4">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-[#1E3A8A]"></div>
                  <h3 className="font-serif font-bold text-[#1E3A8A] text-base tracking-wide">AFFIRMATIVE (PRO)</h3>
                </div>
                {activeSpeaker === 'PRO' && (
                  <span className="text-[11px] font-mono text-[#1E3A8A] bg-blue-50 px-2 py-0.5 rounded border border-blue-200 animate-pulse">
                    Presenting...
                  </span>
                )}
              </div>

              <div className="space-y-4">
                {proArguments.length === 0 ? (
                  <p className="text-xs text-[#A8A7A1] italic py-8 text-center">Awaiting affirmative opening...</p>
                ) : (
                  proArguments.map((arg, idx) => {
                    const audit = proAudits[idx];
                    const isExpanded = expandedArgId === `pro_${idx}`;
                    return (
                      <div key={idx} className="border border-[#E6E4DD] rounded-lg p-4 bg-[#FAFAF8] space-y-2.5 text-left transition hover:border-[#D5D3CB]">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-mono uppercase tracking-wider text-[#73726E] font-medium">
                            Round {arg.round_number} · {arg.argument_type}
                          </span>
                          {audit && (
                            <span className="inline-flex items-center gap-1 text-[11px] font-mono text-emerald-800 bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded">
                              <ShieldCheck className="w-3 h-3 text-emerald-700" /> Audit Pass ({Math.round((audit.logical_strength_score || 0.8) * 100)}%)
                            </span>
                          )}
                        </div>

                        {arg.target_claim_id && (
                          <div className="text-[11px] font-mono text-[#73726E] bg-white border border-[#E6E4DD] px-2 py-1 rounded flex items-center gap-1">
                            <CornerDownRight className="w-3 h-3 text-[#1E3A8A]" />
                            <span>Rebutting: {arg.target_claim_id}</span>
                          </div>
                        )}

                        <h4 className="text-sm font-semibold text-[#1A1A1A] leading-snug">
                          {arg.claim}
                        </h4>

                        <p className="text-xs text-[#52514D] leading-relaxed">
                          {arg.reasoning}
                        </p>

                        <div className="text-xs bg-blue-50/50 border border-blue-100 rounded p-2 text-[#1E3A8A]">
                          <span className="font-semibold font-mono text-[10px] uppercase block mb-0.5">Societal Impact:</span>
                          {arg.impact}
                        </div>

                        {/* Expandable Evidence Card */}
                        {arg.source_citation && (
                          <div className="pt-2 border-t border-[#E6E4DD]/60 flex items-center justify-between text-[11px]">
                            <a
                              href={arg.source_citation}
                              target="_blank"
                              rel="noreferrer"
                              className="text-[#1E3A8A] hover:underline flex items-center gap-1 font-mono truncate max-w-[280px]"
                            >
                              <BookOpen className="w-3 h-3 text-[#73726E]" />
                              <span className="truncate">{arg.source_citation}</span>
                              <ExternalLink className="w-2.5 h-2.5 opacity-60" />
                            </a>
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* CON Podium */}
            <div className="bg-white border border-[#E6E4DD] rounded-xl p-5 shadow-xs">
              <div className="flex items-center justify-between border-b border-[#E6E4DD] pb-3 mb-4">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-[#991B1B]"></div>
                  <h3 className="font-serif font-bold text-[#991B1B] text-base tracking-wide">OPPOSITION (CON)</h3>
                </div>
                {activeSpeaker === 'CON' && (
                  <span className="text-[11px] font-mono text-[#991B1B] bg-rose-50 px-2 py-0.5 rounded border border-rose-200 animate-pulse">
                    Presenting...
                  </span>
                )}
              </div>

              <div className="space-y-4">
                {conArguments.length === 0 ? (
                  <p className="text-xs text-[#A8A7A1] italic py-8 text-center">Awaiting opposition opening...</p>
                ) : (
                  conArguments.map((arg, idx) => {
                    const audit = conAudits[idx];
                    return (
                      <div key={idx} className="border border-[#E6E4DD] rounded-lg p-4 bg-[#FAFAF8] space-y-2.5 text-left transition hover:border-[#D5D3CB]">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-mono uppercase tracking-wider text-[#73726E] font-medium">
                            Round {arg.round_number} · {arg.argument_type}
                          </span>
                          {audit && (
                            <span className="inline-flex items-center gap-1 text-[11px] font-mono text-emerald-800 bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded">
                              <ShieldCheck className="w-3 h-3 text-emerald-700" /> Audit Pass ({Math.round((audit.logical_strength_score || 0.8) * 100)}%)
                            </span>
                          )}
                        </div>

                        {arg.target_claim_id && (
                          <div className="text-[11px] font-mono text-[#73726E] bg-white border border-[#E6E4DD] px-2 py-1 rounded flex items-center gap-1">
                            <CornerDownRight className="w-3 h-3 text-[#991B1B]" />
                            <span>Rebutting: {arg.target_claim_id}</span>
                          </div>
                        )}

                        <h4 className="text-sm font-semibold text-[#1A1A1A] leading-snug">
                          {arg.claim}
                        </h4>

                        <p className="text-xs text-[#52514D] leading-relaxed">
                          {arg.reasoning}
                        </p>

                        <div className="text-xs bg-rose-50/50 border border-rose-100 rounded p-2 text-[#991B1B]">
                          <span className="font-semibold font-mono text-[10px] uppercase block mb-0.5">Counter Impact:</span>
                          {arg.impact}
                        </div>

                        {arg.source_citation && (
                          <div className="pt-2 border-t border-[#E6E4DD]/60 flex items-center justify-between text-[11px]">
                            <a
                              href={arg.source_citation}
                              target="_blank"
                              rel="noreferrer"
                              className="text-[#991B1B] hover:underline flex items-center gap-1 font-mono truncate max-w-[280px]"
                            >
                              <BookOpen className="w-3 h-3 text-[#73726E]" />
                              <span className="truncate">{arg.source_citation}</span>
                              <ExternalLink className="w-2.5 h-2.5 opacity-60" />
                            </a>
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            </div>

          </div>

          {/* Referee Clash / Fact Check Review Banner */}
          {clashes.length > 0 && (
            <div className="bg-white border border-[#E6E4DD] rounded-xl p-5 shadow-xs">
              <span className="text-[10px] font-mono tracking-wider uppercase text-[#73726E] font-medium block mb-2">
                REFEREE EMPIRICAL REVIEW & CLASH RESOLUTION
              </span>
              <div className="space-y-2">
                {clashes.map((clash, i) => (
                  <div key={i} className="bg-[#FAFAF8] border border-[#E6E4DD] p-3.5 rounded-lg text-xs flex flex-col gap-1">
                    <div className="flex justify-between items-center text-[#52514D] font-mono text-[11px]">
                      <span>Round {clash.round_number || (i + 1)} Alignment Review</span>
                      <span className={clash.has_direct_conflict ? 'text-amber-800' : 'text-emerald-800'}>
                        {clash.has_direct_conflict ? '• Factual Clash Resolved' : '• Complementary Premises'}
                      </span>
                    </div>
                    <p className="text-[#1A1A1A] leading-relaxed mt-1">
                      <span className="font-medium text-[#73726E] font-mono">Ground Truth: </span>
                      {clash.empirical_ground_truth}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Final Adjudication (Formal Editorial Verdict) */}
          {adjudication && (
            <div className="bg-white border border-[#1E3A8A]/30 rounded-xl p-6 shadow-sm">
              <span className="text-[10px] font-mono tracking-wider uppercase text-[#1E3A8A] font-semibold block mb-1">
                FINAL COURT ADJUDICATION
              </span>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-[#E6E4DD] pb-4 mb-4 gap-2">
                <h3 className="text-xl font-serif font-bold text-[#1A1A1A]">
                  Ruling in Favor of: <span className={String(adjudication.winner).includes('PRO') ? 'text-[#1E3A8A]' : 'text-[#991B1B]'}>{String(adjudication.winner).replace('WinnerSide.', '')}</span>
                </h3>
                <div className="flex items-center gap-4 text-xs font-mono">
                  <span className="text-[#1E3A8A] font-medium">
                    PRO: {adjudication.judge_verdict?.pro_scorecard?.total_score ?? adjudication.judge_verdict?.pro_score ?? 60} pts
                  </span>
                  <span className="text-[#73726E]">|</span>
                  <span className="text-[#991B1B] font-medium">
                    CON: {adjudication.judge_verdict?.con_scorecard?.total_score ?? adjudication.judge_verdict?.con_score ?? 80} pts
                  </span>
                </div>
              </div>

              <div className="text-xs text-[#52514D] leading-relaxed space-y-2">
                <span className="font-semibold text-[#1A1A1A] font-mono uppercase text-[10px] block">
                  Adjudicator Rationale:
                </span>
                <p className="font-serif text-sm text-[#1A1A1A] leading-relaxed italic bg-[#FAFAF8] p-4 rounded-lg border border-[#E6E4DD]">
                  "{adjudication.judge_verdict?.rationale || adjudication.judge_verdict?.reasoning || adjudication.judge_verdict?.adjudication_rationale || 'Adjudication completed based on empirical evidence and argument strength.'}"
                </p>
              </div>
            </div>
          )}

        </div>
      )}

    </div>
  );
}