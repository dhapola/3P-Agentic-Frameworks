import logging
from typing import Dict, List, Any
from langgraph.graph import END, StateGraph
from app.libs.utils import get_or_create_clients
from app.libs.types import GraphState
from app.libs.nodes import (
    router_preprocess, 
    llm_router, 
    prepare_analysis,
    perform_reasoning,
    tool_executor, 
    direct_response,
    process_file,
    visualize_data
)

logger = logging.getLogger(__name__)

_compiled_graph = None

def create_workflow_graph():
    """
    Create and compile the workflow graph for processing financial queries.
    Uses singleton pattern for efficient reuse.
    """
    global _compiled_graph
    
    if _compiled_graph is not None:
        return _compiled_graph
        
    logger.info("Compiling workflow graph")
    graph = StateGraph(GraphState)
    
    graph.add_node("router_preprocess", router_preprocess)
    graph.add_node("llm_router", llm_router)
    graph.add_node("prepare_analysis", prepare_analysis)
    graph.add_node("perform_reasoning", perform_reasoning)
    graph.add_node("tool_executor", tool_executor)
    graph.add_node("process_file", process_file)
    graph.add_node("visualize_data", visualize_data)
    graph.add_node("direct_response", direct_response)
    
    graph.set_entry_point("router_preprocess")
    
    graph.add_conditional_edges(
        "router_preprocess",
        lambda state: state["route_to"]
    )
    
    graph.add_conditional_edges(
        "llm_router",
        lambda state: 
            "prepare_analysis" if state["route_to"] == "financial_analysis" 
            else "visualize_data" if state["route_to"] == "visualize_data" 
            else state["route_to"]
    )
    
    graph.add_edge("process_file", "visualize_data")
    graph.add_edge("visualize_data", END)
    
    graph.add_edge("prepare_analysis", "perform_reasoning")
    
    graph.add_conditional_edges(
        "perform_reasoning",
        lambda state: state.get("next", END)
    )
    
    graph.add_edge("tool_executor", "perform_reasoning")
    graph.add_edge("direct_response", END)
    
    _compiled_graph = graph.compile()
    return _compiled_graph

async def process_messages_with_graph(
    state: Dict,
    model: str,
    region: str,
    thought_callback=None,
    session_id: str = None,
    config: Dict = None
) -> Dict[str, Any]:
    """
    Process messages through the LangGraph workflow.
    Uses dependency injection to avoid circular imports.
    """
    try:
        clients = get_or_create_clients(region)
        
        # Resolve the graph - either use the global instance or create a new one
        local_graph = _get_or_create_graph_instance()
        
        # Use ConversationMemoryManager for state persistence instead of LangGraph sessions
        final_state = await local_graph.ainvoke(state)
        
        answer = final_state.get("answer", "I wasn't able to generate a response.")
        
        answering_tool_map = {
            "file_processing": "file",
            "process_file": "file",
            "visualize_data": "visualization",
            "direct_response": "chat"  
        }
        
        last_active_node = final_state.get("metadata", {}).get("last_active_node")
        answering_tool = answering_tool_map.get(last_active_node, "chat")
        
        return {
            "name": "session_completed",
            "input": {
                "answering_tool": "financial",
                "direct_answer": answer,
                "session_id": session_id
            }
        }
    
    except Exception as e:
        logger.error(f"Error in workflow execution: {str(e)}", exc_info=True) 

        return {
            "name": "session_terminated",
            "input": {
                "answering_tool": "financial",
                "direct_answer": f"Error processing request: {str(e)}",
                "session_id": session_id
            }
        }

def _get_or_create_graph_instance():
    """
    Helper function to get the workflow graph instance.
    Uses dependency injection pattern to avoid circular imports.
    """
    try:
        # Dynamically import to avoid circular dependency
        import importlib
        app_module = importlib.import_module('app.app')
        workflow_graph_instance = getattr(app_module, 'workflow_graph', None)
        
        if workflow_graph_instance is None:
            logger.warning("Global workflow graph not found, creating new instance")
            return create_workflow_graph()
        return workflow_graph_instance
    except ImportError:
        logger.warning("Could not import app module, creating new graph instance")
        return create_workflow_graph()