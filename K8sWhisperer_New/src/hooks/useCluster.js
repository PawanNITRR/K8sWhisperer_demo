import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

// Dev: empty string → same-origin requests hit Vite proxy (vite.config.js).
// Prod / preview: full URL unless VITE_API_URL is set at build time.
const defaultApiUrl =
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL) ||
  (typeof import.meta !== 'undefined' && import.meta.env?.DEV ? '' : 'http://localhost:8080');

const useCluster = (apiUrl = defaultApiUrl) => {
  const [loading, setLoading] = useState(true);
  const [pods, setPods] = useState([]);
  const [currentStage, setCurrentStage] = useState(0); 
  const [remediation, setRemediation] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);

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

      setLoading(false);
    } catch (err) {
      console.error("Connection Error:", err);
      setLoading(false);
    }
  }, [apiUrl]);

  useEffect(() => {
    fetchData();
    // Use a shorter interval if we are in the 'Execute' phase to show resolution 
    const intervalTime = currentStage === 5 ? 5000 : 30000; 
    const interval = setInterval(fetchData, intervalTime); 
    return () => clearInterval(interval);
  }, [fetchData, currentStage]);

  return { 
    pods, currentStage, remediation, auditLogs, loading,
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
    refresh: fetchData 
  };
};

export default useCluster;