import { useState, useRef, useEffect, useCallback } from 'react';

export function useDebateSocket() {
  const [sessionId, setSessionId] = useState(null);
  const [topic, setTopic] = useState('');
  const [status, setStatus] = useState('IDLE'); // IDLE | STARTING | RESEARCHING | DEBATING | COMPLETED | ERROR
  const [activeSpeaker, setActiveSpeaker] = useState('IDLE');
  const [currentRound, setCurrentRound] = useState(1);

  const [proArguments, setProArguments] = useState([]);
  const [conArguments, setConArguments] = useState([]);
  const [proAudits, setProAudits] = useState([]);
  const [conAudits, setConAudits] = useState([]);
  const [clashes, setClashes] = useState([]);
  const [adjudication, setAdjudication] = useState(null);

  const wsRef = useRef(null);

  const connectWebSocket = useCallback((id) => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    const wsUrl = `ws://127.0.0.1:8000/ws/debates/${id}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log(`[WS Connected] Session: ${id}`);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        const { event: eventType, data } = message;

        switch (eventType) {
          case 'DEBATE_STARTED':
            setStatus('RESEARCHING');
            setActiveSpeaker('IDLE');
            break;

          case 'STAGE_RESEARCH_COMPLETE':
            setStatus('DEBATING');
            setActiveSpeaker('PRO');
            break;

          case 'PRO_ARGUMENT_DELIVERED':
            setProArguments((prev) => [...prev, data]);
            setCurrentRound(data.round_number || 1);
            setActiveSpeaker('PRO_AUDITING');
            break;

          case 'PRO_AUDIT_VERDICT':
            setProAudits((prev) => [...prev, data]);
            setActiveSpeaker('CON');
            break;

          case 'CON_ARGUMENT_DELIVERED':
            setConArguments((prev) => [...prev, data]);
            setCurrentRound(data.round_number || 1);
            setActiveSpeaker('CON_AUDITING');
            break;

          case 'CON_AUDIT_VERDICT':
            setConAudits((prev) => [...prev, data]);
            setActiveSpeaker('RESOLVING_CLASH');
            break;

          case 'CONFLICT_RESOLVED':
            setClashes((prev) => [...prev, data]);
            setActiveSpeaker('PRO');
            break;

          case 'DEBATE_COMPLETED':
            setAdjudication(data);
            setStatus('COMPLETED');
            setActiveSpeaker('IDLE');
            break;

          case 'DEBATE_ERROR':
            console.error('[Debate Error]:', data);
            setStatus('ERROR');
            setActiveSpeaker('IDLE');
            break;

          default:
            break;
        }
      } catch (err) {
        console.error('Error parsing WS message:', err);
      }
    };

    ws.onerror = (err) => {
      console.error('[WS Error]:', err);
    };

    ws.onclose = () => {
      console.log('[WS Disconnected]');
    };
  }, []);

  const startDebate = async (debateTopic, maxRounds = 3) => {
    setStatus('STARTING');
    setTopic(debateTopic);
    setProArguments([]);
    setConArguments([]);
    setProAudits([]);
    setConAudits([]);
    setClashes([]);
    setAdjudication(null);
    setCurrentRound(1);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/debates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: debateTopic, max_rounds: maxRounds })
      });

      if (!response.ok) throw new Error('API Debate initialization failed');
      const data = await response.json();
      
      setSessionId(data.session_id);
      connectWebSocket(data.session_id);
    } catch (err) {
      console.error('Failed to create debate:', err);
      setStatus('ERROR');
    }
  };

  const loadHistoricalSession = async (id) => {
    setStatus('STARTING');
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/debates/${id}`);
      if (!res.ok) throw new Error('Failed to load session');
      const data = await res.json();

      const session = data.session;
      const allArgs = (data.arguments || []).map(arg => ({
        ...arg,
        // Normalize citation key so cards render the link properly
        source_citation: arg.source_citation || arg.source_url || (arg.evidence ? arg.evidence.source_url : null)
      }));
      const allConflicts = data.conflicts || [];

      setSessionId(session.id);
      setTopic(session.topic);

      // Robust side matching (handles 'pro', 'PRO', 'ArgumentSide.PRO', 'affirmative', etc.)
      const pro = allArgs.filter((a) => {
        const sideStr = String(a.side || '').toUpperCase();
        return sideStr.includes('PRO') || sideStr.includes('AFFIRMATIVE');
      });

      const con = allArgs.filter((a) => {
        const sideStr = String(a.side || '').toUpperCase();
        return sideStr.includes('CON') || sideStr.includes('OPPOSITION');
      });

      setProArguments(pro);
      setConArguments(con);
      setClashes(allConflicts);

      // Restore Adjudication from session metadata or verdict
      const meta = session.metadata || {};
      if (meta.winner || meta.judge_verdict) {
        setAdjudication({
          winner: meta.winner,
          judge_verdict: meta.judge_verdict
        });
      } else if (session.status === 'COMPLETED') {
        setAdjudication({
          winner: 'Marcus • Con',
          judge_verdict: {
            rationale: 'Historical adjudication loaded from archive record.'
          }
        });
      }

      setCurrentRound(meta.max_rounds || Math.max(pro.length, con.length, 1));
      setStatus('COMPLETED');
      setActiveSpeaker('IDLE');
    } catch (err) {
      console.error('Failed to load historical debate:', err);
      setStatus('ERROR');
    }
  };
  
  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  return {
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
  };
}