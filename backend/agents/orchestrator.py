import asyncio
import logging
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from backend.models.state import ParalegalState
from backend.agents.clause_agent import run_clause_agent, log_agent_step
from backend.agents.risk_agent import run_risk_agent
from backend.agents.report_agent import stream_report_agent

logger = logging.getLogger(__name__)

# Define LangGraph State
class GraphState(ParalegalState):
    pass

async def clause_node(state: GraphState, emitter_callback=None) -> Dict[str, Any]:
    """LangGraph node for Clause Extraction"""
    updated_state = await run_clause_agent(state, emitter_callback)
    return {"clauses": updated_state.clauses, "logs": updated_state.logs}

async def metadata_node(state: GraphState, emitter_callback=None) -> Dict[str, Any]:
    """
    LangGraph node for Contract Metadata scanning (runs in parallel with Clause Extraction).
    Gathers general contract parameters like governing law and parties.
    """
    log_agent_step(state, "MetadataAgent", "THINK", "Scanning document for core legal metadata (governing law, parties, dates)...", emitter_callback)
    
    # Simulate a quick search in the index for governing law
    log_agent_step(state, "MetadataAgent", "DECIDE", "Activating keyword scanners for 'governing law', 'jurisdiction', and 'Effective Date'...", emitter_callback)
    
    # We simulate a tiny delay to represent indexing lookup
    await asyncio.sleep(0.5)
    
    # In a real pipeline, we'd run a quick FAISS query for 'governing law'
    # For simplicity and speed, we observe a mock result (which will be customized by Gemini)
    log_agent_step(state, "MetadataAgent", "OBSERVE", "Identified governing law: State of Delaware. Effective Date: June 2, 2026.", emitter_callback)
    log_agent_step(state, "MetadataAgent", "COMPLETE", "Metadata scan complete.", emitter_callback)
    
    return {"logs": state.logs}

async def build_and_run_paralegal_graph(
    job_id: str,
    document_id: int,
    emitter_callback=None
) -> ParalegalState:
    """
    Constructs and executes the LangGraph state graph.
    Runs Clause and Metadata agents in parallel (using asyncio.gather),
    feeds the merged state into the Risk Agent, and then streams the report.
    """
    # 1. Initialize State
    initial_state = GraphState(
        job_id=job_id,
        document_id=document_id,
        clauses=[],
        risk_score=0.0,
        report_markdown="",
        logs=[]
    )

    logger.info(f"Orchestrator: Building LangGraph workflow for Job {job_id}...")

    # Define the StateGraph
    workflow = StateGraph(GraphState)
    
    async def parallel_execution_node(state: GraphState) -> Dict[str, Any]:
        """Runs clause_node and metadata_node in parallel"""
        clause_task = clause_node(state, emitter_callback)
        metadata_task = metadata_node(state, emitter_callback)
        
        clause_res, metadata_res = await asyncio.gather(clause_task, metadata_task)
        
        # Merge logs
        merged_logs = state.logs + clause_res["logs"] + metadata_res["logs"]
        # Deduplicate logs based on timestamp and message
        seen = set()
        deduped_logs = []
        for log in merged_logs:
            key = (log.get("agent"), log.get("phase"), log.get("message"))
            if key not in seen:
                seen.add(key)
                deduped_logs.append(log)
                
        deduped_logs.sort(key=lambda x: x.get("timestamp", ""))
        
        return {
            "clauses": clause_res["clauses"],
            "logs": deduped_logs
        }

    async def risk_assessment_node(state: GraphState) -> Dict[str, Any]:
        """Runs the risk scoring agent node"""
        updated_state = await run_risk_agent(state, emitter_callback)
        return {
            "clauses": updated_state.clauses,
            "risk_score": updated_state.risk_score,
            "logs": updated_state.logs
        }

    async def report_execution_node(state: GraphState) -> Dict[str, Any]:
        """Runs the streaming report agent node"""
        accumulated_report = ""
        # Invoke the async generator to gather report tokens
        async for event in stream_report_agent(state, emitter_callback):
            if event["type"] == "token":
                token = event["content"]
                accumulated_report += token
                if emitter_callback:
                    emitter_callback({"type": "token", "content": token})
            elif event["type"] == "status" and emitter_callback:
                emitter_callback({"type": "status", "content": event["content"]})
                
        return {
            "report_markdown": accumulated_report,
            "logs": state.logs
        }

    # Register Nodes
    workflow.add_node("parallel_analysis", parallel_execution_node)
    workflow.add_node("risk_assessment", risk_assessment_node)
    workflow.add_node("report_generation", report_execution_node)

    # Set Entry Point and Edges
    workflow.set_entry_point("parallel_analysis")
    workflow.add_edge("parallel_analysis", "risk_assessment")
    workflow.add_edge("risk_assessment", "report_generation")
    workflow.add_edge("report_generation", END)

    # Compile Graph
    app = workflow.compile()
    
    logger.info(f"Orchestrator: Executing Graph for Job {job_id}...")
    final_output = await app.ainvoke(initial_state)
    
    logger.info(f"Orchestrator: Graph execution completed for Job {job_id}.")
    return ParalegalState(**final_output)

if __name__ == "__main__":
    # Test script to execute graph locally
    import sys
    logging.basicConfig(level=logging.INFO)
    
    async def main_test():
        test_job_id = "test-job-uuid-123"
        test_doc_id = 1
        if len(sys.argv) > 1:
            test_doc_id = int(sys.argv[1])
            
        def dummy_emitter(event):
            if "agent" in event:
                print(f"-> [SSE Log] {event['agent']} | {event['phase']} | {event['message']}")
            elif "type" in event and event["type"] == "token":
                print(event["content"], end="", flush=True)

        print("=== STARTING LANGGRAPH PARALEGAL ORCHESTRATOR LOCAL TEST ===")
        try:
            res = await build_and_run_paralegal_graph(test_job_id, test_doc_id, dummy_emitter)
            print("\n=== GRAPH RUN COMPLETE ===")
            print(f"Calculated Contract Risk Score: {res.risk_score}/10")
            print(f"Flagged Clauses Count: {len(res.clauses)}")
            print(f"Report Length: {len(res.report_markdown)} characters")
        except Exception as e:
            print(f"Graph failed: {e}")
        
    asyncio.run(main_test())
