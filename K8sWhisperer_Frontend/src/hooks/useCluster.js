import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { logIncidentToBlockchain } from '../integration';

const defaultApiUrl =
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL) ||
  (typeof process !== 'undefined' && process.env?.REACT_APP_API_URL) ||
  'http://localhost:8080';

const useCluster = (apiUrl = defaultApiUrl) => {
  const [loading, setLoading] = useState(true);
  const [pods, setPods] = useState([]);
  const [currentStage, setCurrentStage] = useState(0);
  const [remediation, setRemediation] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const lastLoggedRef = useRef(null);

  const fetchData = useCallback(async () => {
    try {
      const response = await axios.get(`${apiUrl}/state`);
      const data = response.data;

      setPods(data.pods || []);

      const stageMap = {
        observe: 0,
        detect: 1,
        diagnose: 2,
        plan: 3,
        safety_gate: 4,
        hitl: 4,
        execute: 5,
        alert_decision: 5,
        explain: 6,
      };
      const stageIdx = stageMap[data.current_node] || 0;
      setCurrentStage(stageIdx);

      if (data.hitl_thread_id && data.plan && data.approved !== true) {
        setRemediation({ ...data.plan, thread_id: data.hitl_thread_id });
      } else {
        setRemediation(null);
      }

      setAuditLogs(data.audit_log || []);

      if (stageIdx === 6 && data.audit_log?.length > 0) {
        const latestEntry = data.audit_log[data.audit_log.length - 1];
        if (lastLoggedRef.current !== latestEntry.timestamp) {
          logIncidentToBlockchain(latestEntry);
          lastLoggedRef.current = latestEntry.timestamp;
        }
      }

      setLoading(false);
    } catch (err) {
      console.error('Connection Error:', err);
      setLoading(false);
    }
  }, [apiUrl]);

  useEffect(() => {
    fetchData();
    const intervalTime = currentStage === 5 ? 5000 : 30000;
    const interval = setInterval(fetchData, intervalTime);
    return () => clearInterval(interval);
  }, [fetchData, currentStage]);

  return {
    pods,
    currentStage,
    remediation,
    auditLogs,
    loading,
    approve: () =>
      axios.post(`${apiUrl}/slack/interactive`, {
        action: 'approve',
        thread_id: remediation?.thread_id,
      }),
    reject: () =>
      axios.post(`${apiUrl}/slack/interactive`, {
        action: 'reject',
        thread_id: remediation?.thread_id,
      }),
    refresh: fetchData,
  };
};

export default useCluster;
