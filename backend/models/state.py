from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AgentLog(BaseModel):
    agent: str  # "ClauseAgent", "RiskAgent", "ReportAgent"
    phase: str  # "THINK", "DECIDE", "ACT", "OBSERVE", "REPEAT", "COMPLETE"
    message: str
    timestamp: str

class ParalegalState(BaseModel):
    job_id: str = Field(..., description="Unique job ID for tracking")
    document_id: int = Field(..., description="Database ID of the ingested document")
    
    # Extracted clauses from PDF via RAG
    # Format of each clause dict:
    # {
    #   "chunk_id": int,
    #   "text": str,
    #   "page_num": int,
    #   "block_num": int,
    #   "score": float,            # Semantic match score
    #   "risk_score": float,       # Evaluated risk weight (0 to 10)
    #   "risk_level": str,         # "Low", "Medium", "High", "Critical"
    #   "risk_category": str,      # Category from lexicon (e.g. "Indemnification")
    #   "risk_explanation": str    # Explanation of risk
    # }
    clauses: List[Dict[str, Any]] = Field(default_factory=list, description="List of extracted clauses with risk scores")
    
    # Risk assessment
    risk_score: float = Field(0.0, description="Overall contract risk rating (1 to 10)")
    
    # Generated Markdown analysis report
    report_markdown: str = Field("", description="Final aggregated report markdown written by report_agent")
    
    # Execution tracing logs
    logs: List[Dict[str, Any]] = Field(default_factory=list, description="Reasoning logs representing the Think-Decide-Act steps")
    
    # Helper metadata
    error: Optional[str] = None
