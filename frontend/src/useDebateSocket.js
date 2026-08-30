import { useState, useEffect, useRef, useCallback } from 'react';

export function useDebateSocket() {
  const [sessionId, setSessionId] = useState(null);
  const [topic, setTopic] = useState('');
  const [status, setStatus] = useState('IDLE'); // IDLE, RESEARCHING, DEBATING, COMPLETED, ERROR
  const [proArguments, setProArguments] = useState([]);
  const [conArguments, setConArguments] = useState([]);
  const [proAudits, setProAudits] = useState([]);
  const [conAudits, setConAudits] = useState([]);
  const [clashes, setClashes] = useState([]);
  const [adjudication, setAdjudication] = useState(null);
  const [currentRound, setCurrentRound] = useState(1);
  const [activeSpeaker, setActiveSpeaker] = useState(null);

  const socketRef = useRef(null);

  const startDebate = async (debateTopic, maxRounds = 2) => {
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

      const data = await response.json();
      setSessionId(data.session_id);
      connectWebSocket(data.session_id);
    } catch (err) {
      console.error('Failed to create debate:', err);
      setStatus('ERROR');
    }
  };

  const connectWebSocket = useCallback((id) => {
    if (socketRef.current) {
      socketRef.current.close();
    }

    const ws = new WebSocket(`ws://127.0.0.1:8000/ws/debates/${id}`);
    socketRef.current = ws;

    ws.onopen = () => {
      console.log('Connected to debate live stream:', id);
    };

    ws.onmessage = (event) => {
      try {
        const { event: eventType, data } = JSON.parse(event.data);
        console.log('Live WS Event:', eventType, data);

        switch (eventType) {
          case 'DEBATE_STARTED':
            setStatus('RESEARCHING');
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
            setActiveSpeaker(null);
            break;

          case 'DEBATE_ERROR':
            setStatus('ERROR');
            break;

          default:
            break;
        }
      } catch (err) {
        console.error('WS Parse error:', err);
      }
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
      setStatus('ERROR');
    };
  }, []);

  useEffect(() => {
    return () => {
      if (socketRef.current) socketRef.current.close();
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
    startDebate
  };
}