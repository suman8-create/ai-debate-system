import React, { useState, useEffect } from 'react';
import { useDebateSocket } from './useDebateSocket';
import { 
  History, 
  Plus, 
  X, 
  Search, 
  Scale, 
  CheckCircle2, 
  Clock, 
  ChevronRight,
  ArrowUpRight
} from 'lucide-react';

export default function App() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [topicInput, setTopicInput] = useState("Universities should require students to disclose AI assistance in assessed work.");
  const [roundsCount, setRoundsCount] = useState(3);
  const [historyList, setHistoryList] = useState([]);
  const [historySearch, setHistorySearch] = useState('');

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
    startDebate,
    loadHistoricalSession
  } = useDebateSocket();

  const maxRounds = Number(roundsCount) || 3;
  const isLive = status === 'RESEARCHING' || status === 'DEBATING' || status === 'STARTING';

  const fetchHistory = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/debates/history');
      if (res.ok) {
        const data = await res.json();
        setHistoryList(data);
      }
    } catch (e) {
      console.error('History fetch error:', e);
    }
  };

  useEffect(() => {
    if (isHistoryOpen) {
      fetchHistory();
    }
  }, [isHistoryOpen]);

  const handleLaunch = (e) => {
    e?.preventDefault();
    if (!topicInput.trim()) return;
    setIsModalOpen(false);
    startDebate(topicInput.trim(), maxRounds);
  };

  const currentTopic = topic || topicInput;

  return (
    <div className="min-h-screen bg-[#F4F1EA] text-[#222] font-sans antialiased flex flex-col selection:bg-stone-300">
      
      {/* Top Editorial Navbar */}
      <header className="w-full border-b border-[#E3DFD5] bg-[#F4F1EA] px-6 py-3.5 flex items-center justify-between sticky top-0 z-30">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[#2E2B27] text-[#F4F1EA] flex items-center justify-center font-serif font-bold text-sm shadow-xs">
            ⚔
          </div>
          <div>
            <span className="font-serif font-bold text-base tracking-tight text-[#1A1816] block leading-none">
              The Adversarial
            </span>
            <span className="text-[10px] font-mono tracking-widest text-[#7C776E] uppercase">
              AI Debate Workspace
            </span>
          </div>
        </div>

        {/* Engine Status & Action Controls */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 text-xs font-mono text-[#666] bg-[#ECE7DC] px-3 py-1.5 rounded-full border border-[#DFDAD0]">
            <span className={`w-2 h-2 rounded-full ${isLive ? 'bg-amber-600 animate-pulse' : 'bg-emerald-600'}`} />
            <span>{isLive ? 'Dialectic in session' : 'Analysis engine ready'}</span>
          </div>

          <button
            onClick={() => setIsHistoryOpen(true)}
            className="flex items-center gap-1.5 text-xs font-medium text-[#4A463F] hover:text-[#1A1816] bg-[#ECE7DC] hover:bg-[#E4DFD3] border border-[#DFDAD0] px-3 py-1.5 rounded-lg transition cursor-pointer"
          >
            <History className="w-3.5 h-3.5" />
            <span>History</span>
          </button>

          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-1.5 text-xs font-medium text-[#F4F1EA] bg-[#2E2B27] hover:bg-[#1A1816] px-3.5 py-1.5 rounded-lg transition shadow-xs cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New debate</span>
          </button>
        </div>
      </header>

      {/* Main Workspace Canvas */}
      <main className="flex-1 max-w-6xl w-full mx-auto p-6 md:p-8 space-y-8">
        
        {/* Topic Header & Category Pill */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-[11px] font-mono tracking-wider text-[#7C776E] uppercase">
            <span className="bg-[#EAE5D9] px-2 py-0.5 rounded border border-[#DDD7CB]">ACADEMIC INQUIRY</span>
            <span>•</span>
            <span>Live Workspace</span>
          </div>
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-serif font-normal text-[#1A1816] tracking-tight leading-[1.18]">
            {currentTopic}
          </h1>
        </div>

        {/* Round Progress Horizontal Stepper */}
        <div className="w-full border-t border-b border-[#E3DFD5] py-3 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3 overflow-x-auto">
            {Array.from({ length: maxRounds }).map((_, idx) => {
              const rNum = idx + 1;
              const isReviewed = rNum < currentRound || status === 'COMPLETED';
              const isCurrent = rNum === currentRound && isLive;
              return (
                <div
                  key={idx}
                  className={`flex items-center gap-1.5 text-xs font-mono px-3 py-1 rounded-full border transition ${
                    isCurrent
                      ? 'bg-[#E5D7CE] border-[#8C4A32] text-[#8C4A32] font-semibold'
                      : isReviewed
                      ? 'bg-[#ECE7DC] border-[#DFDAD0] text-[#555]'
                      : 'bg-transparent border-transparent text-[#9E988D]'
                  }`}
                >
                  <span className={`w-1.5 h-1.5 rounded-full ${isCurrent ? 'bg-[#8C4A32]' : isReviewed ? 'bg-emerald-600' : 'bg-[#BBB5A8]'}`} />
                  <span>Round {rNum}</span>
                  <span className="text-[10px] uppercase tracking-wider opacity-80">
                    {isCurrent ? 'CURRENT' : isReviewed ? 'REVIEWED' : 'QUEUED'}
                  </span>
                </div>
              );
            })}
          </div>

          <div className="text-xs font-mono text-[#7C776E] flex items-center gap-1">
            <span>Round {Math.min(currentRound, maxRounds)} of {maxRounds}</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </div>
        </div>

        {/* Live Active Pipeline Status Bar */}
        {isLive && (
          <div className="bg-[#ECE7DC] border border-[#DDD7CB] p-3.5 rounded-xl flex items-center justify-between text-xs font-mono shadow-2xs">
            <div className="flex items-center gap-2.5 text-[#8C4A32]">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#8C4A32] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#8C4A32]"></span>
              </span>
              <span className="font-medium">
                {status === 'RESEARCHING' && 'Research Agent: Ingesting web evidence & vectorizing...'}
                {activeSpeaker === 'PRO' && 'Athena (PRO): Generating constructive/rebuttal case...'}
                {activeSpeaker === 'PRO_AUDITING' && 'Auditor: Stress-testing PRO claims for fallacies...'}
                {activeSpeaker === 'CON' && 'Marcus (CON): Synthesizing opposition counter-case...'}
                {activeSpeaker === 'CON_AUDITING' && 'Auditor: Verifying CON evidence credibility...'}
                {activeSpeaker === 'RESOLVING_CLASH' && 'Referee: Fact-checking empirical clashes...'}
                {(!activeSpeaker || activeSpeaker === 'IDLE') && status !== 'RESEARCHING' && 'Debate engine active...'}
              </span>
            </div>
            <span className="text-[#7C776E] bg-[#DFDAD0] px-2.5 py-0.5 rounded-md">
              Round {Math.min(currentRound, maxRounds)} of {maxRounds}
            </span>
          </div>
        )}

        {/* Split-Screen Arena Podiums */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
          
          {/* Athena (PRO / AFFIRMATIVE) */}
          <div className="bg-[#FAF8F4] border border-[#E3DFD5] rounded-xl p-6 space-y-6 shadow-2xs">
            {/* Header Persona */}
            <div className="flex items-center justify-between border-b border-[#ECE7DC] pb-4">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-[#EAD8CD] text-[#8C4A32] font-serif font-bold text-sm flex items-center justify-center border border-[#D5C2B4]">
                  A
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-serif font-bold text-base text-[#1A1816]">Athena</span>
                    <span className="text-[10px] font-mono uppercase bg-[#ECE7DC] text-[#666] px-1.5 py-0.5 rounded border border-[#DDD7CB]">
                      AFFIRMATIVE
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-[#7C776E] mt-0.5">
                    {activeSpeaker === 'PRO' ? (
                      <span className="text-[#8C4A32] font-medium flex items-center gap-1">
                        <span className="w-2 h-2 rounded-full bg-[#8C4A32] animate-ping" /> Speaking...
                      </span>
                    ) : (
                      <span>Waiting</span>
                    )}
                  </div>
                </div>
              </div>

              <div className="text-right">
                {adjudication?.judge_verdict?.pro_scorecard?.total_score || proAudits.length > 0 ? (
                  <>
                    <span className="text-xl font-mono font-bold text-[#1A1816]">
                      {adjudication?.judge_verdict?.pro_scorecard?.total_score ?? Math.round((proAudits[proAudits.length - 1]?.logical_strength_score || 0) * 100)}
                    </span>
                    <span className="text-xs font-mono text-[#888]">/100</span>
                  </>
                ) : (
                  <span className="text-xs font-mono text-[#9E988D]">—</span>
                )}
                <span className="text-[10px] font-mono text-[#7C776E] block">{proArguments.length} ARGUMENTS</span>
              </div>
            </div>

            {/* Arguments Feed */}
            {proArguments.length === 0 ? (
              <p className="text-xs font-serif text-[#A09A8F] italic text-center py-12">
                Awaiting Athena to present the opening constructive case...
              </p>
            ) : (
              proArguments.map((arg, idx) => {
                const audit = proAudits[idx];
                return (
                  <div key={idx} className="space-y-4 border-b border-[#ECE7DC] pb-5 last:border-0 last:pb-0">
                    <div>
                      <span className="text-[10px] font-mono tracking-widest text-[#8C4A32] uppercase font-semibold block mb-1">
                        MAIN CLAIM • ROUND {arg.round_number}
                      </span>
                      <h3 className="font-serif text-lg font-semibold text-[#1A1816] leading-snug">
                        {arg.claim}
                      </h3>
                    </div>

                    <div>
                      <span className="text-[10px] font-mono tracking-wider text-[#7C776E] uppercase block mb-1">
                        SUPPORTING REASONING
                      </span>
                      <p className="text-xs text-[#4A463F] leading-relaxed font-sans">
                        {arg.reasoning}
                      </p>
                    </div>

                    <div className="bg-[#F2ECE3] border border-[#E4DDD1] p-2.5 rounded-lg text-xs text-[#6A3926]">
                      <span className="font-mono text-[10px] uppercase font-bold block mb-0.5">Projected Impact:</span>
                      {arg.impact}
                    </div>

                    {arg.source_citation && (
                      <div>
                        <span className="text-[10px] font-mono tracking-wider text-[#7C776E] uppercase block mb-1.5">
                          EVIDENCE REFERENCES
                        </span>
                        <a
                          href={arg.source_citation}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1.5 text-xs font-mono text-[#1A1816] bg-[#ECE7DC] hover:bg-[#E4DFD3] border border-[#DDD7CB] px-2.5 py-1 rounded-md transition"
                        >
                          <span className="truncate max-w-[220px]">{arg.source_citation}</span>
                          <ArrowUpRight className="w-3 h-3 text-[#7C776E]" />
                        </a>
                      </div>
                    )}

                    {audit && (
                      <div className="pt-2 flex items-center justify-between text-xs font-mono text-[#555]">
                        <span className="text-[10px] uppercase tracking-wider text-[#7C776E]">Auditor Review:</span>
                        <span className="text-emerald-800 font-semibold bg-emerald-100/70 border border-emerald-300 px-2 py-0.5 rounded">
                          {audit.verdict} ({Math.round(audit.logical_strength_score * 100)}% Logic)
                        </span>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>

          {/* Marcus (CON / OPPOSITION) */}
          <div className="bg-[#FAF8F4] border border-[#E3DFD5] rounded-xl p-6 space-y-6 shadow-2xs">
            {/* Header Persona */}
            <div className="flex items-center justify-between border-b border-[#ECE7DC] pb-4">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-[#CCD8D5] text-[#2B544C] font-serif font-bold text-sm flex items-center justify-center border border-[#B3C5C1]">
                  M
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-serif font-bold text-base text-[#1A1816]">Marcus</span>
                    <span className="text-[10px] font-mono uppercase bg-[#ECE7DC] text-[#666] px-1.5 py-0.5 rounded border border-[#DDD7CB]">
                      OPPOSITION
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-[#7C776E] mt-0.5">
                    {activeSpeaker === 'CON' ? (
                      <span className="text-[#2B544C] font-medium flex items-center gap-1">
                        <span className="w-2 h-2 rounded-full bg-[#2B544C] animate-ping" /> Speaking...
                      </span>
                    ) : (
                      <span>Waiting</span>
                    )}
                  </div>
                </div>
              </div>

              <div className="text-right">
                {adjudication?.judge_verdict?.con_scorecard?.total_score || conAudits.length > 0 ? (
                  <>
                    <span className="text-xl font-mono font-bold text-[#1A1816]">
                      {adjudication?.judge_verdict?.con_scorecard?.total_score ?? Math.round((conAudits[conAudits.length - 1]?.logical_strength_score || 0) * 100)}
                    </span>
                    <span className="text-xs font-mono text-[#888]">/100</span>
                  </>
                ) : (
                  <span className="text-xs font-mono text-[#9E988D]">—</span>
                )}
                <span className="text-[10px] font-mono text-[#7C776E] block">{conArguments.length} ARGUMENTS</span>
              </div>
            </div>

            {/* Arguments Feed */}
            {conArguments.length === 0 ? (
              <p className="text-xs font-serif text-[#A09A8F] italic text-center py-12">
                Awaiting Marcus to present the opposition counter-case...
              </p>
            ) : (
              conArguments.map((arg, idx) => {
                const audit = conAudits[idx];
                return (
                  <div key={idx} className="space-y-4 border-b border-[#ECE7DC] pb-5 last:border-0 last:pb-0">
                    <div>
                      <span className="text-[10px] font-mono tracking-widest text-[#2B544C] uppercase font-semibold block mb-1">
                        MAIN CLAIM • ROUND {arg.round_number}
                      </span>
                      <h3 className="font-serif text-lg font-semibold text-[#1A1816] leading-snug">
                        {arg.claim}
                      </h3>
                    </div>

                    <div>
                      <span className="text-[10px] font-mono tracking-wider text-[#7C776E] uppercase block mb-1">
                        SUPPORTING REASONING
                      </span>
                      <p className="text-xs text-[#4A463F] leading-relaxed font-sans">
                        {arg.reasoning}
                      </p>
                    </div>

                    <div className="bg-[#E4ECE9] border border-[#D1DDD9] p-2.5 rounded-lg text-xs text-[#20423B]">
                      <span className="font-mono text-[10px] uppercase font-bold block mb-0.5">Counter Impact:</span>
                      {arg.impact}
                    </div>

                    {arg.source_citation && (
                      <div>
                        <span className="text-[10px] font-mono tracking-wider text-[#7C776E] uppercase block mb-1.5">
                          EVIDENCE REFERENCES
                        </span>
                        <a
                          href={arg.source_citation}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1.5 text-xs font-mono text-[#1A1816] bg-[#ECE7DC] hover:bg-[#E4DFD3] border border-[#DDD7CB] px-2.5 py-1 rounded-md transition"
                        >
                          <span className="truncate max-w-[220px]">{arg.source_citation}</span>
                          <ArrowUpRight className="w-3 h-3 text-[#7C776E]" />
                        </a>
                      </div>
                    )}

                    {audit && (
                      <div className="pt-2 flex items-center justify-between text-xs font-mono text-[#555]">
                        <span className="text-[10px] uppercase tracking-wider text-[#7C776E]">Auditor Review:</span>
                        <span className="text-emerald-800 font-semibold bg-emerald-100/70 border border-emerald-300 px-2 py-0.5 rounded">
                          {audit.verdict} ({Math.round(audit.logical_strength_score * 100)}% Logic)
                        </span>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Audit & Metrics Comparison Bar */}
        {(proAudits.length > 0 || conAudits.length > 0) && (
          <div className="bg-[#FAF8F4] border border-[#E3DFD5] rounded-xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-[#ECE7DC] pb-3">
              <div>
                <span className="text-[10px] font-mono tracking-widest text-[#7C776E] uppercase block">02 • AUDIT</span>
                <h3 className="font-serif font-bold text-lg text-[#1A1816]">Comparative Argument Audit</h3>
              </div>
              <span className="text-xs font-mono text-[#666] bg-[#ECE7DC] px-2.5 py-1 rounded-full border border-[#DDD7CB]">
                Balanced Review
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-2">
              <div className="space-y-3">
                <span className="text-xs font-mono font-semibold text-[#8C4A32] uppercase">Athena (PRO) Metrics</span>
                <div className="space-y-2">
                  {(() => {
                    const latestProAudit = proAudits[proAudits.length - 1];
                    const proScore = latestProAudit ? Math.round(latestProAudit.logical_strength_score * 100) : 0;
                    return (
                      <>
                        <div className="flex justify-between text-xs font-mono">
                          <span className="text-[#666]">Logical & Factual Strength</span>
                          <span className="font-bold">{proScore}%</span>
                        </div>
                        <div className="w-full bg-[#E5D7CE]/40 rounded-full h-1.5">
                          <div className="bg-[#8C4A32] h-1.5 rounded-full transition-all duration-500" style={{ width: `${proScore}%` }}></div>
                        </div>
                      </>
                    );
                  })()}
                </div>
              </div>

              <div className="space-y-3">
                <span className="text-xs font-mono font-semibold text-[#2B544C] uppercase">Marcus (CON) Metrics</span>
                <div className="space-y-2">
                  {(() => {
                    const latestConAudit = conAudits[conAudits.length - 1];
                    const conScore = latestConAudit ? Math.round(latestConAudit.logical_strength_score * 100) : 0;
                    return (
                      <>
                        <div className="flex justify-between text-xs font-mono">
                          <span className="text-[#666]">Logical & Factual Strength</span>
                          <span className="font-bold">{conScore}%</span>
                        </div>
                        <div className="w-full bg-[#CCD8D5]/40 rounded-full h-1.5">
                          <div className="bg-[#2B544C] h-1.5 rounded-full transition-all duration-500" style={{ width: `${conScore}%` }}></div>
                        </div>
                      </>
                    );
                  })()}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Referee Clash / Fact Check Review Banner */}
        {clashes.length > 0 && (
          <div className="bg-[#FAF8F4] border border-[#E3DFD5] rounded-xl p-6 space-y-3 shadow-2xs">
            <span className="text-[10px] font-mono tracking-wider uppercase text-[#7C776E] font-medium block">
              REFEREE EMPIRICAL REVIEW & CLASH RESOLUTION
            </span>
            <div className="space-y-2.5">
              {clashes.map((clash, i) => (
                <div key={i} className="bg-[#F4F1EA] border border-[#E3DFD5] p-3.5 rounded-lg text-xs flex flex-col gap-1">
                  <div className="flex justify-between items-center text-[#555] font-mono text-[11px]">
                    <span>Round {clash.round_number || (i + 1)} Alignment Review</span>
                    <span className={clash.has_direct_conflict ? 'text-amber-800' : 'text-emerald-800'}>
                      {clash.has_direct_conflict ? '• Factual Clash Resolved' : '• Complementary Premises'}
                    </span>
                  </div>
                  <p className="text-[#1A1816] leading-relaxed mt-1">
                    <span className="font-medium text-[#7C776E] font-mono">Ground Truth: </span>
                    {clash.empirical_ground_truth}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* The Deciding Exchange (Adjudication Sealed) */}
        {adjudication && (
          <div className="space-y-3">
            <span className="text-[10px] font-mono tracking-widest text-[#7C776E] uppercase block">
              03 • ROUND SUMMARY & VERDICT
            </span>
            <div className="bg-[#282622] text-[#F4F1EA] rounded-xl p-6 sm:p-8 space-y-4 shadow-md">
              <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-[#D6CEBF]">
                <CheckCircle2 className="w-4 h-4 text-[#D6CEBF]" />
                <span>Round Winner</span>
              </div>

              <h3 className="text-2xl sm:text-3xl font-serif font-bold text-white tracking-tight">
                {String(adjudication.winner).includes('PRO') ? 'Athena • Pro' : 'Marcus • Con'}
              </h3>

              <p className="font-serif text-sm sm:text-base text-[#DCD7CB] leading-relaxed italic border-l-2 border-[#8C4A32] pl-4 py-1">
                "{adjudication.judge_verdict?.rationale || adjudication.judge_verdict?.reasoning || 'The prevailing agent paired empirical evidence with substantive counter-rebuttal analysis to resolve the central tension.'}"
              </p>
            </div>
          </div>
        )}
      </main>

      {/* New Debate Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-[#FAF8F4] border border-[#DFDAD0] rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5 animate-fade-in">
            <div className="flex items-center justify-between border-b border-[#ECE7DC] pb-3">
              <div>
                <h3 className="font-serif font-bold text-xl text-[#1A1816]">Set up a new debate</h3>
                <p className="text-xs text-[#7C776E] mt-0.5">
                  Give the editorial room a statement to pressure-test.
                </p>
              </div>
              <button onClick={() => setIsModalOpen(false)} className="text-[#888] hover:text-[#222]">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleLaunch} className="space-y-4">
              <div>
                <label className="text-[10px] font-mono uppercase tracking-wider text-[#7C776E] block mb-1.5 font-bold">
                  DEBATE STATEMENT
                </label>
                <textarea
                  rows={3}
                  value={topicInput}
                  onChange={(e) => setTopicInput(e.target.value)}
                  placeholder="e.g. Universities should require students to disclose AI assistance..."
                  className="w-full bg-[#F4F1EA] border border-[#DDD7CB] rounded-xl p-3 text-sm font-serif focus:outline-none focus:border-[#2E2B27] resize-none"
                />
              </div>

              <div>
                <label className="text-[10px] font-mono uppercase tracking-wider text-[#7C776E] block mb-1.5 font-bold">
                  NUMBER OF ROUNDS (1 - 8)
                </label>
                <input
                  type="number"
                  min={1}
                  max={8}
                  value={roundsCount}
                  onChange={(e) => setRoundsCount(e.target.value)}
                  className="w-24 bg-[#F4F1EA] border border-[#DDD7CB] rounded-lg px-3 py-2 text-xs font-mono focus:outline-none focus:border-[#2E2B27]"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#ECE7DC]">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="text-xs font-medium text-[#7C776E] hover:text-[#1A1816] px-4 py-2"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-[#2E2B27] hover:bg-[#1A1816] text-[#F4F1EA] text-xs font-medium px-5 py-2.5 rounded-xl transition flex items-center gap-1.5 shadow-xs cursor-pointer"
                >
                  <span>Create workspace</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* History Archive Drawer */}
      {isHistoryOpen && (
        <div className="fixed inset-0 z-50 flex justify-start bg-black/30 backdrop-blur-xs">
          <div className="bg-[#FAF8F4] border-r border-[#DFDAD0] w-full max-w-sm h-full p-6 shadow-2xl flex flex-col space-y-5 animate-slide-in">
            <div className="flex items-center justify-between border-b border-[#ECE7DC] pb-3">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-widest text-[#7C776E]">ARCHIVE</span>
                <h3 className="font-serif font-bold text-xl text-[#1A1816]">Past debates</h3>
              </div>
              <button onClick={() => setIsHistoryOpen(false)} className="text-[#888] hover:text-[#222]">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Search filter */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-3 text-[#9E988D]" />
              <input
                type="text"
                placeholder="Search sessions..."
                value={historySearch}
                onChange={(e) => setHistorySearch(e.target.value)}
                className="w-full bg-[#F4F1EA] border border-[#DDD7CB] rounded-xl pl-9 pr-3 py-2 text-xs font-mono focus:outline-none"
              />
            </div>

            {/* Session List */}
            <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
              {historyList.length === 0 ? (
                <p className="text-xs text-[#A09A8F] italic text-center py-8">
                  No historical debates recorded.
                </p>
              ) : (
                historyList
                  .filter(h => !historySearch || h.topic?.toLowerCase().includes(historySearch.toLowerCase()))
                  .map((session, idx) => (
                    <div
                      key={session.id || idx}
                      onClick={() => {
                        loadHistoricalSession(session.id);
                        setIsHistoryOpen(false);
                      }}
                      className="bg-[#F4F1EA] hover:bg-[#ECE7DC] border border-[#DDD7CB] p-3.5 rounded-xl cursor-pointer transition space-y-2"
                    >
                      <h4 className="font-serif text-sm font-semibold text-[#1A1816] leading-snug line-clamp-2">
                        {session.topic}
                      </h4>
                      <div className="flex items-center justify-between text-[10px] font-mono text-[#7C776E]">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {session.created_at ? new Date(session.created_at).toLocaleDateString() : 'Recent'}
                        </span>
                        <span className="text-[#8C4A32] font-semibold flex items-center gap-0.5">
                          Open <ChevronRight className="w-3 h-3" />
                        </span>
                      </div>
                    </div>
                  ))
              )}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}