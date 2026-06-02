import logging
from typing import Dict, Any, List
from backend.models.state import ParalegalState
from backend.tools.risk_lexicon import RISK_LEXICON, get_lexicon_term_meta
from backend.agents.clause_agent import log_agent_step

logger = logging.getLogger(__name__)

def evaluate_clause_risk(clause_text: str, query_category: str, semantic_score: float) -> tuple[float, str, str, str]:
    """
    Evaluates risk score, category, level, and explanation for a given clause text.
    First tries exact phrase matching from the lexicon.
    Falls back to semantic query category matching if no direct text match is found.
    """
    matched_lexicon_items = []
    
    # 1. Direct text search for lexicon terms
    for item in RISK_LEXICON:
        if item["term"].lower() in clause_text.lower():
            matched_lexicon_items.append(item)
            
    if matched_lexicon_items:
        # Sort by weight descending to find the most severe risk term in the clause
        matched_lexicon_items.sort(key=lambda x: x["weight"], reverse=True)
        top_match = matched_lexicon_items[0]
        
        score = top_match["weight"]
        category = top_match["category"]
        explanation = top_match["explanation"]
    else:
        # 2. Fall back to semantic score mapping based on the query category
        # Find the term in the lexicon that matches the query category
        category_items = [i for i in RISK_LEXICON if i["category"] == query_category]
        if category_items:
            category_items.sort(key=lambda x: x["weight"], reverse=True)
            top_cat = category_items[0]
            # Scale score based on semantic similarity
            score = round(top_cat["weight"] * semantic_score, 1)
            category = query_category
            explanation = f"Semantically related to {top_cat['term']} risk category. {top_cat['explanation']}"
        else:
            score = round(3.0 * semantic_score, 1)
            category = "General"
            explanation = "Presents potential legal liabilities. Requires manual review."

    # Determine risk level name
    if score < 4.0:
        level = "Low"
    elif score < 7.0:
        level = "Medium"
    elif score < 9.0:
        level = "High"
    else:
        level = "Critical"
        
    return score, category, level, explanation

async def run_risk_agent(state: ParalegalState, emitter_callback=None) -> ParalegalState:
    """
    Risk Agent: Evaluates risk for each extracted clause, assigns scores/levels/explanations,
    and computes the overall contract risk rating.
    """
    log_agent_step(state, "RiskAgent", "THINK", f"Analyzing risk posture of {len(state.clauses)} clauses...", emitter_callback)
    
    if not state.clauses:
        state.risk_score = 1.0
        log_agent_step(state, "RiskAgent", "OBSERVE", "No risk clauses identified. Assigning baseline risk score of 1.0.", emitter_callback)
        log_agent_step(state, "RiskAgent", "COMPLETE", "Risk analysis finalized.", emitter_callback)
        return state
        
    scored_clauses = []
    
    for idx, clause in enumerate(state.clauses):
        # 1. THINK
        log_agent_step(state, "RiskAgent", "THINK", f"Evaluating clause {idx+1}/{len(state.clauses)} on Page {clause['page_num']}.", emitter_callback)
        
        # 2. DECIDE & ACT
        score, category, level, explanation = evaluate_clause_risk(
            clause["text"], 
            clause["risk_category"], 
            clause["score"]
        )
        
        # 3. OBSERVE
        log_agent_step(
            state, 
            "RiskAgent", 
            "OBSERVE", 
            f"Clause {idx+1} classified as [{level} Risk] (Score: {score}) under '{category}'.", 
            emitter_callback
        )
        
        scored_clause = clause.copy()
        scored_clause["risk_score"] = score
        scored_clause["risk_category"] = category
        scored_clause["risk_level"] = level
        scored_clause["risk_explanation"] = explanation
        scored_clauses.append(scored_clause)
        
    # Sort clauses by risk score descending
    scored_clauses.sort(key=lambda x: x["risk_score"], reverse=True)
    state.clauses = scored_clauses
    
    # 4. Compute overall contract risk rating
    # We take the average of the top 3 highest clause scores to determine the overall contract risk
    top_scores = [c["risk_score"] for c in state.clauses[:3]]
    if len(top_scores) == 0:
        overall_score = 1.0
    else:
        overall_score = round(sum(top_scores) / len(top_scores), 1)
        
    # Bounds check
    state.risk_score = max(1.0, min(10.0, overall_score))
    
    log_agent_step(
        state, 
        "RiskAgent", 
        "OBSERVE", 
        f"Overall Contract Risk Score calculated as: {state.risk_score}/10 (based on top severe clauses).", 
        emitter_callback
    )
    
    log_agent_step(state, "RiskAgent", "COMPLETE", "Contract risk profiling successfully finalized.", emitter_callback)
    return state
