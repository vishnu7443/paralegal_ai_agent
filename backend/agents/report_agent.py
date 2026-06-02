import os
import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, List
from backend.models.state import ParalegalState
from backend.agents.clause_agent import log_agent_step

logger = logging.getLogger(__name__)

def generate_local_markdown_report(state: ParalegalState) -> str:
    """
    Generates a premium, highly detailed contract risk analysis report locally.
    Used as an ultra-reliable, high-fidelity fallback.
    """
    risk_score = state.risk_score
    risk_level = "Low" if risk_score < 4.0 else "Medium" if risk_score < 7.0 else "High" if risk_score < 9.0 else "Critical"
    
    # Categorize clauses
    critical_count = sum(1 for c in state.clauses if c["risk_level"] == "Critical")
    high_count = sum(1 for c in state.clauses if c["risk_level"] == "High")
    med_count = sum(1 for c in state.clauses if c["risk_level"] == "Medium")
    
    report = []
    report.append(f"# EXECUTIVE LEGAL RISK ANALYSIS REPORT")
    report.append(f"**Generated on:** {datetime.utcnow().strftime('%B %d, %Y')} | **Analyst Crew:** Antigravity Paralegal AI Agent\n")
    report.append(f"## 1. Executive Summary")
    report.append(f"This contract risk report compiles qualitative and semantic analysis of your uploaded legal document. Our AI agent crew has scanned the text, matched sections against 20+ risk vectors in the legal lexicon, and formulated a comprehensive risk profile.")
    report.append(f"- **Overall Contract Risk Rating:** `{risk_score}/10` (**{risk_level} Risk**)")
    report.append(f"- **Total Flagged Clauses:** {len(state.clauses)} instances")
    report.append(f"- **Severity Breakdown:** `{critical_count}` Critical | `{high_count}` High | `{med_count}` Medium\n")
    
    report.append(f"## 2. High-Risk Clause Directory")
    report.append(f"Below is the prioritized directory of clauses representing potential liability or unfavourable terms:")
    report.append(f"| Page | Category | Risk Level | Score | Flagged Clause Snippet |")
    report.append(f"| :--- | :--- | :--- | :--- | :--- |")
    
    for c in state.clauses[:10]:  # Show top 10 clauses in table
        snippet = c["text"][:100].replace("\n", " ") + "..."
        report.append(f"| Page {c['page_num']} | {c['risk_category']} | **{c['risk_level']}** | `{c['risk_score']}` | {snippet} |")
        
    report.append("\n## 3. Deep-Dive Qualitative Risks & Vulnerabilities")
    for idx, c in enumerate(state.clauses[:5]):  # Detailed analysis of top 5
        report.append(f"### Vulnerability #{idx+1}: {c['risk_category']} (Page {c['page_num']}, Score: {c['risk_score']})")
        report.append(f"**Clause Text:**")
        report.append(f"> \"{c['text']}\"")
        report.append(f"**Risk Implication:**")
        report.append(f"{c['risk_explanation']}")
        report.append("")
        
    report.append("## 4. Strategic Recommendations")
    report.append("Based on the contract's risk score of `" + str(risk_score) + "/10`, we recommend the following negotiation actions:")
    
    if risk_score >= 7.0:
        report.append("- [ ] **Insert Liability Cap**: Add a reciprocal limitation of liability clause capped at 12 months fees or a specific dollar amount.")
        report.append("- [ ] **Carve out Mutual Indemnification**: Convert unilateral indemnities into mutual ones, and carve out negligence or willful misconduct.")
        report.append("- [ ] **Restrict IP Assignment**: Limit IP assignment to final, paid deliverables. Avoid broad 'work for hire' language on background IP.")
        report.append("- [ ] **Add Mutual Termination**: Add a 30-day termination for convenience clause for both parties to balance the unilateral termination threat.")
    elif risk_score >= 4.0:
        report.append("- [ ] **Clarify Indemnity Scope**: Narrow down the scope of indemnification to direct third-party intellectual property infringement claims.")
        report.append("- [ ] **Review Automatic Renewals**: Ensure automatic renewal notices must be sent at least 30 days prior to term expiration.")
    else:
        report.append("- [ ] **Verify Venue and Jurisdiction**: The contract has low risk, but confirm that the exclusive jurisdiction matches your local state courts to avoid travel expenses.")
        
    report.append("\n*Disclaimer: This analysis is compiled by an AI Agent Crew for demo purposes and does not constitute formal legal advice. Consultation with a qualified attorney is recommended for final contract reviews.*")
    
    return "\n".join(report)

async def stream_report_agent(state: ParalegalState, emitter_callback=None) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Streams the compiled report using Google Gemini API
    or falls back to a highly realistic template-driven streaming experience.
    Yields dictionary events: {"type": "token"|"status", "content": str}
    """
    # 1. THINK
    log_agent_step(state, "ReportAgent", "THINK", "Evaluating collected risk scores and clause citations to synthesize the contract brief.", emitter_callback)
    
    # 2. DECIDE
    api_key = os.getenv("GEMINI_API_KEY")
    use_gemini = api_key and api_key != "mock_key" and api_key != "your_gemini_api_key_here"
    
    if use_gemini:
        log_agent_step(state, "ReportAgent", "DECIDE", "Activating Google Gemini API via official SDK to stream custom contract risk synthesis.", emitter_callback)
    else:
        log_agent_step(state, "ReportAgent", "DECIDE", "No valid Gemini API key found. Activating premium local analytics generator fallback.", emitter_callback)
        
    # 3. ACT
    log_agent_step(state, "ReportAgent", "ACT", "Drafting legal analysis brief and streaming output tokens...", emitter_callback)
    
    if use_gemini:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            # Format state context for LLM prompt
            prompt_context = {
                "document_id": state.document_id,
                "overall_risk_score": state.risk_score,
                "flagged_clauses": [
                    {
                        "text": c["text"],
                        "page": c["page_num"],
                        "category": c["risk_category"],
                        "risk_score": c["risk_score"],
                        "risk_level": c["risk_level"],
                        "explanation": c["risk_explanation"]
                    }
                    for c in state.clauses[:15]  # Limit to top 15 to save context window space
                ]
            }
            
            system_prompt = (
                "You are an elite corporate legal counsel and contract risk officer. "
                "Write a highly professional, comprehensive legal risk analysis report in Markdown. "
                "Use an objective, premium, analytical legal tone. Analyze the overall risk rating, the specific "
                "clause exposures, the severity levels, and jurisdiction details. "
                "Structure the report clearly with markdown headings, tables, blockquotes, and a recommendations checklist."
            )
            
            model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_prompt)
            user_message = f"Here is the collected real-time contract intelligence:\n\n{prompt_context}\n\nPlease write the executive analysis report."
            
            # Call Gemini stream
            response = model.generate_content(user_message, stream=True)
            
            accumulated_report = ""
            for chunk in response:
                if chunk.text:
                    token = chunk.text
                    accumulated_report += token
                    yield {"type": "token", "content": token}
                    # Small sleep for smooth streaming
                    await asyncio.sleep(0.005)
            
            state.report_markdown = accumulated_report
            
        except Exception as e:
            logger.error(f"Gemini Streaming Error: {e}. Falling back to local reporter...")
            log_agent_step(state, "ReportAgent", "OBSERVE", f"Gemini call failed ({e}). Falling back to local reporter.", emitter_callback)
            use_gemini = False  # Triggers local fallback
            
    if not use_gemini:
        # Local high-quality mock stream to guarantee beautiful mock experience
        full_report = generate_local_markdown_report(state)
        
        # Split report into smaller word tokens to simulate a super fast, premium streaming experience
        words = full_report.split(" ")
        accumulated_report = ""
        
        # Stream in batches of 4 words for optimal responsiveness
        batch_size = 4
        for i in range(0, len(words), batch_size):
            token = " ".join(words[i:i+batch_size]) + " "
            accumulated_report += token
            yield {"type": "token", "content": token}
            await asyncio.sleep(0.03)  # Smooth flow
            
        state.report_markdown = accumulated_report

    # 4. OBSERVE & 5. COMPLETE
    log_agent_step(state, "ReportAgent", "OBSERVE", "Successfully completed contract analysis brief stream. Document compiled.", emitter_callback)
    log_agent_step(state, "ReportAgent", "COMPLETE", "Agent crew process terminated. State stored in shared memory.", emitter_callback)
    
    yield {"type": "status", "content": "COMPLETE"}
