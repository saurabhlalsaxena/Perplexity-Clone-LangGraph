#search_graph.py
from langgraph.graph import StateGraph, END
from .search_agent_nodes import OverallState
from app.db_setup import checkpointer
#import checkpointer

def create_graph(checkpointer):
    perplexity_clone = StateGraph(OverallState)
    perplexity_clone.add_node('Query Generator',OverallState.search_query_node)
    perplexity_clone.add_node('Search Results',OverallState.search_results_node)
    perplexity_clone.add_node('Web Scraper',OverallState.web_scape_node)
    perplexity_clone.add_node('Generate Summary',OverallState.generate_summary)
    perplexity_clone.add_node('Final Result',OverallState.final_result_node)

    perplexity_clone.set_entry_point('Query Generator')
    perplexity_clone.set_finish_point('Final Result')

    perplexity_clone.add_edge('Query Generator','Search Results')
    perplexity_clone.add_edge('Search Results','Web Scraper')
    perplexity_clone.add_conditional_edges('Web Scraper', OverallState.continue_to_summarise_node,['Generate Summary'])
    perplexity_clone.add_edge('Generate Summary','Final Result')

    perplexity_clone_graph = perplexity_clone.compile(checkpointer=checkpointer)
    return perplexity_clone_graph