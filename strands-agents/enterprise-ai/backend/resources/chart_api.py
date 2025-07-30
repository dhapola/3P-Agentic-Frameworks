import json
from flask_restful import Resource, request
from strands import Agent
from utils.utility import Utility
from strands.models import BedrockModel
from repositories.chat_history_repository import ChatHistoryRepository
import logging

# Set up logging
logger = logging.getLogger(__name__)

class ChartResource(Resource):
    """
    API resource for generating chart configurations based on query results
    """

    def __init__(self):
        self.util = Utility()
        self.chat_history_repo = ChatHistoryRepository()
        

    def post(self):
        data = request.get_json()
        
        model_id = "apac.anthropic.claude-sonnet-4-20250514-v1:0"
        
        # Extract required fields
        text = data.get('text')
        query_results = data.get('queryResults')
        user_id = data.get('user_id', 'Deepesh')  # Default to 'Deepesh' if not provided
        thread_id = data.get('thread_id')
        thread = self.chat_history_repo.get_thread_by_id(thread_id, user_id)
        
        prompt = f"""
            You are a data visualization expert. Based on the following data and analysis, suggest the most appropriate chart type and configuration.
            
            User Query: {text}
            
            Data Results:
            {query_results}
            
            Please provide a JSON response with the following structure:
            {{
                "chart_type": "line|bar|pie|scatter|area|etc",
                "caption": "Brief description of what the chart shows",
                "rationale": "Brief explanation of why this chart type is appropriate",
                "chart_configuration": {{
                "options": {{
                    // ApexCharts options
                }},
                "series": [
                    // ApexCharts series data
                ]
                }}
            }}
            
            Focus on creating a visualization that best represents the data and answers the user's query.
            do not generate formatter functions as these are not parsable by JavaScript
        """

        model = BedrockModel(model_id=model_id, verbose=True, temperature=0.3)

        # Strands Agents SDK allows easy integration of agent tools
        agent = Agent(model=model, tools=[])

        response = agent(prompt)
        # print(f'Chart Code: {response}')

        response = str(response)
        json_response = self.util.clean_json_string(response)

        try:
            ui_msgs = thread['ui_msgs']
            for msg in ui_msgs:
                if msg['human'] == text:
                    msg['graph_code'] = json_response
                    break
            
            # print(f'updated thread: {thread}')
            self.chat_history_repo.save_thread(thread, False)
        except Exception as e:
            logger.error(f"Error updating thread {thread_id} with chart data: {str(e)}")

        self.util.log_data(f'\nFinal Response: {json_response}')
        #chart_dict = json.loads(json_response)

        json_response =  {
            "chart": json_response,
            "status": "success"
        }

        return json_response


                       



                       # If thread_id is provided, try to retrieve the thread from the database
        # if thread_id:
        #     try:
            
        #         thread = self.chat_history_repo.get_thread_by_id(thread_id, user_id)
                
        #         if thread and 'ui_msgs' in thread:
                    
        #             # Find the latest message with query_results
        #             msg = thread['ui_msgs'][-1] # last message

        #             if msg.get('query_results') and msg.get('show_graph'):
        #                 # If the message already has a graph_code, return it
        #                 if msg.get('graph_code') and msg['graph_code'].strip():
        #                     try:
        #                         # Try to parse the graph_code
        #                         chart_data = json.loads(msg['graph_code'])
        #                         logger.info(f"Found existing chart data for thread {thread_id}")
        #                         return {
        #                             "chart": chart_data,
        #                             "status": "success"
        #                         }
        #                     except json.JSONDecodeError:
        #                         # If parsing fails, continue with generating a new chart
        #                         logger.warning(f"Failed to parse existing graph_code for thread {thread_id}")
        #                         pass
                        
        #                 # If no valid graph_code found, use the query_results from the message
        #                 if not query_results and msg.get('query_results'):
        #                     query_results = msg['query_results']
        #                     text = msg.get('human', text)

        #     except Exception as e:
        #         logger.error(f"Error retrieving thread {thread_id}: {str(e)}")
        #         print(f"Error retrieving thread {thread_id}: {str(e)}")
        #         # Continue with the provided query_results
        
        # # Validate required fields
        # if not text:
        #     return {"error": "text is required", "status": "error"}, 400
        # if not query_results:
        #     return {"error": "queryResults is required", "status": "error"}, 400