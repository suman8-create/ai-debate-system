import React, { useState } from 'react';
import { useDebateSocket } from './useDebateSocket';
import { ShieldAlert, CheckCircle2, Award, Zap, BookOpen, AlertTriangle, ArrowRight, RefreshCw } from 'lucide-react';

export default function App() {
  const [inputTopic, setInputTopic] = useState('Should college education be free?');
  const [rounds, setRounds] = useState(2);

  const {
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

  const handleLaunch = (e) => {
    e.preventDefault();
    if (!inputTopic.trim()) return;
    startDebate(inputTopic, rounds);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center p-4 md:p-8">
      {/* Top Header */}
      <header className="w-full max-w-6xl flex items-center justify-between border-b border-slate-800 pb-4 mb-8">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-rose-600 flex items-center justify-center font-bold text-xl shadow-lg shadow-blue-500/20">
            ⚔️
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-purple-300 to-rose-400">
              Autonomous AI Debate Arena
            </h1>
            <p className="text-xs text-slate-400">LangGraph Multi-Agent Dialectic System with Live Auditing</p>
          </div>
        </div>

        {status !== 'IDLE' && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs">
            <span className="relative flex h-2 w-2">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${status === 'COMPLETED' ? 'bg-emerald-400' : 'bg-blue-400'} opacity-75`}></span>
              <span className={`relative inline-flex rounded-full h-2 w-2 ${status === 'COMPLETED' ? 'bg-emerald-500' : 'bg-blue-500'}`}></span>
            </span>
            <span className="font-medium text-slate-300">
              {status === 'RESEARCHING' && 'Researching Web & Indexing...'}
              {status === 'DEBATING' && `Round ${currentRound} in progress`}
              {status === 'COMPLETED' && 'Debate Concluded'}
              {status === 'ERROR' && 'Stream Interrupted'}
            </span>
          </div>
        )}
      </header>

      {/* Topic Input Bar */}
      <div className="w-full max-w-4xl mb-8">
        <form onSubmit={handleLaunch} className="flex flex-col sm:flex-row gap-3 bg-slate-900/80 backdrop-blur p-2 rounded-2xl border border-slate-800 shadow-2xl">
          <input
            type="text"
            value={inputTopic}
            onChange={(e) => setInputTopic(e.target.value)}
            disabled={status === 'RESEARCHING' || status === 'DEBATING'}
            placeholder="Enter debate topic (e.g. Should AI development be paused?)"
            className="flex-1 bg-transparent px-4 py-3 text-sm focus:outline-none placeholder-slate-500 disabled:opacity-50"
          />
          <div className="flex items-center gap-2">
            <select
              value={rounds}
              onChange={(e) => setRounds(Number(e.target.value))}
              disabled={status === 'RESEARCHING' || status === 'DEBATING'}
              className="bg-slate-800 border border-slate-700 text-xs rounded-xl px-3 py-3 focus:outline-none disabled:opacity-50"
            >
              <option value={1}>1 Round</option>
              <option value={2}>2 Rounds</option>
              <option value={3}>3 Rounds</option>
            </select>
            <button
              type="submit"
              disabled={status === 'RESEARCHING' || status === 'DEBATING'}
              className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 font-medium text-sm px-6 py-3 rounded-xl transition shadow-lg shadow-blue-600/30 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {status === 'RESEARCHING' || status === 'DEBATING' ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" /> Live
                </>
              ) : (
                <>
                  Start Arena <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Main Debate Grid: PRO vs CON Podiums */}
      <main className="w-full max-w-6xl grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
        {/* PRO Podium */}
        <section className="bg-slate-900/40 border border-blue-900/30 rounded-2xl p-5 flex flex-col gap-4 shadow-xl">
          <div className="flex items-center justify-between border-b border-blue-900/40 pb-3">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-500 shadow-sm shadow-blue-400"></div>
              <h2 className="font-bold text-blue-400 text-lg">PRO (Affirmative)</h2>
            </div>
            {activeSpeaker?.startsWith('PRO') && (
              <span className="text-xs bg-blue-500/20 text-blue-300 border border-blue-500/30 px-2.5 py-0.5 rounded-full animate-pulse">
                Speaking...
              </span>
            )}
          </div>

          {proArguments.length === 0 ? (
            <p className="text-xs text-slate-500 py-12 text-center italic">Awaiting Affirmative opening statement...</p>
          ) : (
            proArguments.map((arg, idx) => (
              <div key={idx} className="bg-slate-900/90 border border-blue-950 rounded-xl p-4 flex flex-col gap-3 shadow-md">
                <div className="flex items-center justify-between text-xs text-blue-400/80">
                  <span className="font-semibold uppercase tracking-wider">Round {arg.round_number} • {arg.argument_type}</span>
                  {proAudits[idx] && (
                    <span className="flex items-center gap-1 text-emerald-400 bg-emerald-950/40 border border-emerald-900/50 px-2 py-0.5 rounded-md">
                      <CheckCircle2 className="w-3 h-3" /> Audit Pass ({proAudits[idx].logical_strength_score * 100}%)
                    </span>
                  )}
                </div>
                <h3 className="text-sm font-semibold text-slate-200 leading-snug">{arg.claim}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{arg.reasoning}</p>
                <div className="bg-blue-950/30 border border-blue-900/20 rounded-lg p-2.5 text-xs text-blue-200/90">
                  <span className="font-semibold text-blue-300">Impact: </span>{arg.impact}
                </div>
                {arg.source_citation && (
                  <div className="text-[11px] text-slate-500 flex items-center gap-1 truncate">
                    <BookOpen className="w-3 h-3 text-slate-400" />
                    <span>Citation: </span>
                    <a href={arg.source_citation} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline truncate">
                      {arg.source_citation}
                    </a>
                  </div>
                )}
              </div>
            ))
          )}
        </section>

        {/* CON Podium */}
        <section className="bg-slate-900/40 border border-rose-900/30 rounded-2xl p-5 flex flex-col gap-4 shadow-xl">
          <div className="flex items-center justify-between border-b border-rose-900/40 pb-3">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-rose-500 shadow-sm shadow-rose-400"></div>
              <h2 className="font-bold text-rose-400 text-lg">CON (Opposition)</h2>
            </div>
            {activeSpeaker?.startsWith('CON') && (
              <span className="text-xs bg-rose-500/20 text-rose-300 border border-rose-500/30 px-2.5 py-0.5 rounded-full animate-pulse">
                Speaking...
              </span>
            )}
          </div>

          {conArguments.length === 0 ? (
            <p className="text-xs text-slate-500 py-12 text-center italic">Awaiting Opposition opening statement...</p>
          ) : (
            conArguments.map((arg, idx) => (
              <div key={idx} className="bg-slate-900/90 border border-rose-950 rounded-xl p-4 flex flex-col gap-3 shadow-md">
                <div className="flex items-center justify-between text-xs text-rose-400/80">
                  <span className="font-semibold uppercase tracking-wider">Round {arg.round_number} • {arg.argument_type}</span>
                  {conAudits[idx] && (
                    <span className="flex items-center gap-1 text-emerald-400 bg-emerald-950/40 border border-emerald-900/50 px-2 py-0.5 rounded-md">
                      <CheckCircle2 className="w-3 h-3" /> Audit Pass ({conAudits[idx].logical_strength_score * 100}%)
                    </span>
                  )}
                </div>
                <h3 className="text-sm font-semibold text-slate-200 leading-snug">{arg.claim}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{arg.reasoning}</p>
                <div className="bg-rose-950/30 border border-rose-900/20 rounded-lg p-2.5 text-xs text-rose-200/90">
                  <span className="font-semibold text-rose-300">Impact: </span>{arg.impact}
                </div>
                {arg.source_citation && (
                  <div className="text-[11px] text-slate-500 flex items-center gap-1 truncate">
                    <BookOpen className="w-3 h-3 text-slate-400" />
                    <span>Citation: </span>
                    <a href={arg.source_citation} target="_blank" rel="noreferrer" className="text-rose-400 hover:underline truncate">
                      {arg.source_citation}
                    </a>
                  </div>
                )}
              </div>
            ))
          )}
        </section>
      </main>

      {/* Clashes Section */}
      {clashes.length > 0 && (
        <section className="w-full max-w-6xl mt-8 bg-slate-900/80 border border-purple-900/30 rounded-2xl p-5 shadow-xl">
          <div className="flex items-center gap-2 mb-3 text-purple-400 font-bold text-sm">
            <Zap className="w-4 h-4" /> Empirical Fact-Checker & Clash Resolution
          </div>
          <div className="space-y-3">
            {clashes.map((c, i) => (
              <div key={i} className="bg-slate-950/60 border border-purple-950 p-3.5 rounded-xl text-xs flex flex-col gap-1.5">
                <div className="flex justify-between items-center text-slate-400 font-medium">
                  <span>Round {c.round_number} Alignment</span>
                  <span className={c.has_direct_conflict ? 'text-amber-400' : 'text-emerald-400'}>
                    {c.has_direct_conflict ? '⚠️ Direct Conflict Detected' : '✅ Non-Contradictory'}
                  </span>
                </div>
                <p className="text-slate-300 leading-relaxed"><span className="text-purple-300 font-semibold">Ground Truth: </span>{c.empirical_ground_truth}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Final Adjudication Modal / Banner */}
      {adjudication && (
        <section className="w-full max-w-6xl mt-8 bg-gradient-to-b from-slate-900 to-slate-950 border border-amber-500/30 rounded-2xl p-6 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-amber-500/5 rounded-full blur-3xl pointer-events-none"></div>
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2.5 bg-amber-500/20 text-amber-400 rounded-xl">
              <Award className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-100">Final Adjudication & Verdict</h2>
              <p className="text-xs text-amber-400/90 font-medium">Winner: {adjudication.winner}</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div className="bg-blue-950/30 border border-blue-900/40 p-4 rounded-xl text-center">
              <span className="text-xs text-blue-400 font-semibold">PRO Total Score</span>
              <p className="text-2xl font-bold text-blue-200 mt-1">{adjudication.judge_verdict?.pro_scorecard?.total_score || 0} <span className="text-xs text-slate-500 font-normal">/ 100</span></p>
            </div>
            <div className="bg-rose-950/30 border border-rose-900/40 p-4 rounded-xl text-center">
              <span className="text-xs text-rose-400 font-semibold">CON Total Score</span>
              <p className="text-2xl font-bold text-rose-200 mt-1">{adjudication.judge_verdict?.con_scorecard?.total_score || 0} <span className="text-xs text-slate-500 font-normal">/ 100</span></p>
            </div>
          </div>

          <div className="bg-slate-950/80 border border-slate-800 p-4 rounded-xl text-xs text-slate-300 leading-relaxed">
            <span className="font-semibold text-amber-300 block mb-1">Judge Rationale:</span>
            {adjudication.judge_verdict?.rationale}
          </div>
        </section>
      )}
    </div>
  );
}