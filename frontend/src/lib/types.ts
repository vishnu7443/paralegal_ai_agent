export interface AgentLog {
  agent: string;
  phase: string;
  message: string;
  timestamp: string;
}

export interface Clause {
  chunk_id: number;
  text: string;
  page_num: number;
  block_num: number;
  score: number;
  risk_score: number;
  risk_level: 'Low' | 'Medium' | 'High' | 'Critical';
  risk_category: string;
  risk_explanation: string;
}

export interface DocumentResponse {
  id: number;
  filename: string;
  content_text?: string;
  created_at: string;
}

export interface AnalysisJobData {
  id: string;
  document_id: number;
  status: string;
  risk_score: number | null;
  report_markdown: string | null;
  created_at: string;
  completed_at: string | null;
  document?: DocumentResponse;
}

export interface ComparisonItem {
  job_id: string;
  filename: string;
  risk_score: number;
  clause_count: number;
  severity_breakdown: {
    critical: number;
    high: number;
    medium: number;
  };
}
