import { useState, useEffect, useRef, useCallback } from 'react';

const API_BASE = 'http://127.0.0.1:8000';
const WS_BASE = 'ws://127.0.0.1:8000';

/**
 * Client-side display state machine over the debate backend.
 *
 * This hook consumes the existing REST + WebSocket contract exactly as the
 * backend emits it (POST /api/debates, ws /ws/debates/{id}, and the
 * DEBATE_STARTED / STAGE_RESEARCH_COMPLETE / *_ARGUMENT_DELIVERED /
 * *_AUDIT_VERDICT / CONFLICT_RESOLVED / DEBATE_COMPLETED / DEBATE_ERROR
 * events). All added state below is presentational grouping only — no event
 * shapes, endpoints, or payloads are changed.
 */
export function useDebateSocket() {
  const [sessionId, setSessionId] = useState(null);
  const [topic, setTopic] = useState('');
  const [maxRounds, setMaxRounds] = useState(2);
  const [status, setStatus] = useState('IDLE'); // IDLE, STARTING, RESEARCHING, DEBATING, COMPLETED, ERROR
  const [phase, setPhase] = useState('IDLE'); // IDLE, RESEARCH, PRO_DRAFTING, PRO_AUDIT, CON_DRAFTING, CON_AUDIT, CONFLICT, COMPLETE
  const [connectionState, setConnectionState] = useState('idle'); // idle, connecting, open, closed, error
  const [errorMessage, setErrorMessage] = useState(null);

  // Each "turn" groups an argument with its audit + any superseded revisions.
  // Shape: { argument, audit, revisionRequired, history: [{ argument, audit }] }
  const [proTurns, setProTurns] = useState([]);
  const [conTurns, setConTurns] = useState([]);

  const [clashes, setClashes] = useState([]);
  const [adjudication, setAdjudication] = useState(null);
  const [currentRound, setCurrentRound] = useState(1);
  const [activeSpeaker, setActiveSpeaker] = useState(null);

  const socketRef = useRef(null);
  const closedIntentionally = useRef(false);

  const resetState = () => {
    setProTurns([]);
    setConTurns([]);
    setClashes([]);
    setAdjudication(null);
    setCurrentRound(1);
    setActiveSpeaker(null);
    setErrorMessage(null);
    setPhase('IDLE');
  };

  // Append an argument as either a new turn or a revision of the pending one.
  const appendArgument = (setTurns, arg) => {
    setTurns((prev) => {
      const last = prev[prev.length - 1];
      // If the previous turn was flagged for revision and not yet replaced,
      // preserve the original and treat the incoming argument as its revision.
      if (last && last.revisionRequired) {
        const superseded = { argument: last.argument, audit: last.audit };
        const updated = {
          argument: arg,
          audit: null,
          revisionRequired: false,
          history: [...(last.history || []), superseded],
        };
        return [...prev.slice(0, -1), updated];
      }
      return [...prev, { argument: arg, audit: null, revisionRequired: false, history: [] }];
    });
  };

  const attachAudit = (setTurns, audit) => {
    const needsRevision = String(audit?.verdict || '').toUpperCase() === 'REVISE';
    setTurns((prev) => {
      if (prev.length === 0) return prev;
      const updated = [...prev];
      const last = { ...updated[updated.length - 1] };
      last.audit = audit;
      last.revisionRequired = needsRevision;
      updated[updated.length - 1] = last;
      return updated;
    });
    return needsRevision;
  };

  const connectWebSocket = useCallback((id) => {
    if (socketRef.current) {
      closedIntentionally.current = true;
      socketRef.current.close();
    }
    closedIntentionally.current = false;
    setConnectionState('connecting');

    const ws = new WebSocket(`${WS_BASE}/ws/debates/${id}`);
    socketRef.current = ws;

    ws.onopen = () => {
      setConnectionState('open');
    };

    ws.onmessage = (event) => {
      try {
        const { event: eventType, data } = JSON.parse(event.data);

        switch (eventType) {
          case 'DEBATE_STARTED':
            setStatus('RESEARCHING');
            setPhase('RESEARCH');
            if (data?.topic) setTopic(data.topic);
            if (data?.max_rounds) setMaxRounds(data.max_rounds);
            break;

          case 'STAGE_RESEARCH_COMPLETE':
            setStatus('DEBATING');
            setPhase('PRO_DRAFTING');
            setActiveSpeaker('PRO');
            break;

          case 'PRO_ARGUMENT_DELIVERED':
            appendArgument(setProTurns, data);
            setCurrentRound(data.round_number || 1);
            setPhase('PRO_AUDIT');
            setActiveSpeaker('PRO_AUDITING');
            break;

          case 'PRO_AUDIT_VERDICT': {
            const revise = attachAudit(setProTurns, data);
            if (revise) {
              setPhase('PRO_DRAFTING');
              setActiveSpeaker('PRO_REVISING');
            } else {
              setPhase('CON_DRAFTING');
              setActiveSpeaker('CON');
            }
            break;
          }

          case 'CON_ARGUMENT_DELIVERED':
            appendArgument(setConTurns, data);
            setCurrentRound(data.round_number || 1);
            setPhase('CON_AUDIT');
            setActiveSpeaker('CON_AUDITING');
            break;

          case 'CON_AUDIT_VERDICT': {
            const revise = attachAudit(setConTurns, data);
            if (revise) {
              setPhase('CON_DRAFTING');
              setActiveSpeaker('CON_REVISING');
            } else {
              setPhase('CONFLICT');
              setActiveSpeaker('RESOLVING_CLASH');
            }
            break;
          }

          case 'CONFLICT_RESOLVED':
            setClashes((prev) => [...prev, data]);
            setPhase('PRO_DRAFTING');
            setActiveSpeaker('PRO');
            break;

          case 'DEBATE_COMPLETED':
            setAdjudication(data);
            setStatus('COMPLETED');
            setPhase('COMPLETE');
            setActiveSpeaker(null);
            break;

          case 'DEBATE_ERROR':
            setStatus('ERROR');
            setErrorMessage(data?.error || 'The debate stream reported an error.');
            break;

          default:
            break;
        }
      } catch (err) {
        console.error('[v0] WS parse error:', err);
      }
    };

    ws.onerror = () => {
      setConnectionState('error');
    };

    ws.onclose = () => {
      setConnectionState((prev) => (prev === 'error' ? 'error' : 'closed'));
    };
  }, []);

  const startDebate = async (debateTopic, rounds = 2, format = 'STANDARD') => {
    setStatus('STARTING');
    setTopic(debateTopic);
    setMaxRounds(rounds);
    resetState();

    try {
      const response = await fetch(`${API_BASE}/api/debates`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // format is carried for forward-compatibility; the current backend
        // contract only consumes topic + max_rounds and ignores extra fields.
        body: JSON.stringify({ topic: debateTopic, max_rounds: rounds, format }),
      });

      if (!response.ok) throw new Error(`Request failed (${response.status})`);

      const data = await response.json();
      setSessionId(data.session_id);
      connectWebSocket(data.session_id);
    } catch (err) {
      console.error('[v0] Failed to create debate:', err);
      setStatus('ERROR');
      setConnectionState('error');
      setErrorMessage(
        'Could not reach the debate engine. Ensure the backend is running at 127.0.0.1:8000.'
      );
    }
  };

  const reconnect = useCallback(() => {
    if (sessionId) connectWebSocket(sessionId);
  }, [sessionId, connectWebSocket]);

  const reset = () => {
    closedIntentionally.current = true;
    if (socketRef.current) socketRef.current.close();
    setSessionId(null);
    setTopic('');
    setStatus('IDLE');
    setConnectionState('idle');
    resetState();
  };

  useEffect(() => {
    return () => {
      if (socketRef.current) {
        closedIntentionally.current = true;
        socketRef.current.close();
      }
    };
  }, []);

  return {
    sessionId,
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
  };
}
