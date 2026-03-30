export type AnomalyType = 
  | 'CrashLoopBackOff' 
  | 'OOMKilled' 
  | 'PendingPod' 
  | 'EvictedPod' 
  | 'ImagePullBackOff' 
  | 'NodeNotReady' 
  | 'DeploymentStalled' 
  | 'CPUThrottling';

export type StatusType = 'Healthy' | 'Running' | 'Error' | 'Pending' | 'Warning' | 'Critical' | 'Success' | 'Failed' | 'Fail' | 'Pass';

export interface AffectedResource {
  kind: string;
  namespace: string;
  name: string;
}

export interface Anomaly {
  type: AnomalyType;
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  affected_resource: AffectedResource;
  confidence: number;
  trigger_signal?: string;
  notes?: string;
}

export interface Asset {
  name: string;
  type: 'Pod' | 'Deployment' | 'Service' | 'Node' | 'Namespace';
  namespace: string;
  status: StatusType;
  lastUpdated: string;
}

export interface AuditResult {
  id: string;
  name: string;
  status: 'Pass' | 'Fail' | 'Warning';
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  description: string;
  remediation: string;
}

export interface AuditReport {
  timestamp: string;
  clusterContext: string;
  results: AuditResult[];
  summary: {
    totalChecks: number;
    passed: number;
    failed: number;
    severityCounts: {
      critical: number;
      high: number;
      medium: number;
      low: number;
    };
  };
}

export interface NavItem {
  id: string;
  label: string;
  icon: string;
}
