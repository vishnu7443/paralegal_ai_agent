import logging
from datetime import datetime
from typing import Dict, Any, List
from backend.models.state import ParalegalState
from backend.tools.embedder import embedder
from backend.tools.faiss_store import search_index
from backend.tools.risk_lexicon import RISK_LEXICON

logger = logging.getLogger(__name__)

def log_agent_step(state: ParalegalState, agent: str, phase: str, message: str, emitter_callback=None) -> None:
    """Utility to log agent reasoning steps and trigger real-time SSE updates."""
    log_entry = {
        "agent": agent,
        "phase": phase,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    state.logs.append(log_entry)
    logger.info(f"[{agent}][{phase}] {message}")
    
    if emitter_callback:
        try:
            emitter_callback(log_entry)
        except Exception as e:
            logger.warning(f"Failed to emit log: {e}")

async def run_clause_agent(state: ParalegalState, emitter_callback=None) -> ParalegalState:
    """
    Clause Agent: Runs semantic queries against FAISS using top lexicon items,
    retrieves risk-related clauses, and deduplicates them.
    """
    log_agent_step(state, "ClauseAgent", "THINK", "Identifying top 10 risk concepts from the legal lexicon to query the RAG store.", emitter_callback)
    
    # 1. Select the top 10 highest-weight risk terms
    sorted_lexicon = sorted(RISK_LEXICON, key=lambda x: x["weight"], reverse=True)
    query_items = sorted_lexicon[:10]
    
    log_agent_step(
        state, 
        "ClauseAgent", 
        "DECIDE", 
        f"Selected top risk terms for RAG retrieval: {', '.join([i['term'] for i in query_items])}", 
        emitter_callback
    )
    
    log_agent_step(state, "ClauseAgent", "ACT", f"Running semantic queries against local FAISS index for document ID {state.document_id}...", emitter_callback)
    
    unique_clauses: Dict[int, Dict[str, Any]] = {}
    
    for idx, item in enumerate(query_items):
        term = item["term"]
        category = item["category"]
        log_agent_step(state, "ClauseAgent", "THINK", f"[{idx+1}/10] Querying index for '{term}'...", emitter_callback)
        
        try:
            query_vector = embedder.embed_query(term)
            matches = search_index(str(state.document_id), query_vector, k=3)
            
            log_agent_step(state, "ClauseAgent", "OBSERVE", f"Found {len(matches)} matches for '{term}'. Map results...", emitter_callback)
            
            for match in matches:
                chunk_id = match["chunk_id"]
                # Deduplicate by chunk_id, keep the match with higher relevance score
                if chunk_id not in unique_clauses or match["score"] > unique_clauses[chunk_id]["score"]:
                    unique_clauses[chunk_id] = {
                        "chunk_id": chunk_id,
                        "text": match["text"],
                        "page_num": match["page_num"],
                        "block_num": match["block_num"],
                        "score": match["score"],
                        "risk_category": category, # Initialize with the query category
                        "risk_score": 0.0,         # Will be computed by RiskAgent
                        "risk_level": "Low",       # Will be computed by RiskAgent
                        "risk_explanation": ""     # Will be computed by RiskAgent
                    }
        except Exception as e:
            logger.error(f"Error querying term '{term}': {e}", exc_info=True)
            log_agent_step(state, "ClauseAgent", "OBSERVE", f"ERROR: Failed querying '{term}': {str(e)}", emitter_callback)
            
    # Convert back to list
    state.clauses = list(unique_clauses.values())
    
    log_agent_step(
        state, 
        "ClauseAgent", 
        "COMPLETE", 
        f"Clause retrieval finalized. Extracted and deduplicated {len(state.clauses)} legal clauses.", 
        emitter_callback
    )
    return state
