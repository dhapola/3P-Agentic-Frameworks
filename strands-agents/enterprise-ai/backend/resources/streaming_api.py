from flask_restful import Resource
from botocore.exceptions import ClientError, NoCredentialsError
import logging
from providers.bedrock_provider import get_bedrock_client
from utils.utility import Utility
from flask import Response, stream_with_context, request
import queue
import threading
import json
from strands.models import BedrockModel
from strands import Agent, tool
from agents.fintech_sales_postgresql import FintechSalesAgent
from agents.personal_tasks import PersonalTasksAgent
from agents.waf_logs import WAFLogsAgent
from agents.mcp_servers import MCPServersAgent
from flask import session
import time
from utils.chat_thread import ChatThread, ChatThreadHelper
from repositories.chat_history_repository import ChatHistoryRepository
import re

# Set up logging
logger = logging.getLogger(__name__)

class StreamAnswerResource(Resource):

    def __init__(self):
        self.thought_queue = queue.Queue()
        self.util = Utility()
        self.start_time = None
        self.fintech_sales_agent = FintechSalesAgent(self.thought_queue)
        self.personal_tasks_manager = PersonalTasksAgent(self.thought_queue)
        self.mcp_servers_agent = MCPServersAgent(self.thought_queue)
        self.waf_logs_agent = WAFLogsAgent(self.thought_queue)
        self.chat_history_repo = ChatHistoryRepository()
        

    def _answer_stream_response(self, **kwargs):
        self.start_time = time.time()

        # Handle preflight OPTIONS request for CORS
        if request.method == 'OPTIONS':
            response = Response()
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            return response
            
        # Get data from either POST body or GET query parameters
        if request.method == 'POST':
            data = request.json
        else:  # GET
            data = request.args
            
        # Use the new payload structure (human, thread_id, user)
        user_input = data.get('human', '')  # Changed from 'query' to 'human'
        thread_id = data.get('thread_id', '')
        user = data.get('user', 'Deepesh')
        model_id = data.get('model_id', 'anthropic.claude-3-sonnet-20240229-v1:0')
        
        # Log the received data
        logger.info(f"Received request: human={user_input}, thread_id={thread_id}, user={user}, model_id={model_id}")
        
        # Start the processing thread
        threading.Thread(target=self.process_agent_response, args=(user_input, model_id, thread_id, user)).start()
        
        response = Response(stream_with_context(self.generate()), 
                      mimetype='text/event-stream',
                      headers={
                          'Cache-Control': 'no-cache',
                          'Connection': 'keep-alive',
                          'X-Accel-Buffering': 'no',
                          'Access-Control-Allow-Origin': '*',
                          'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                          'Access-Control-Allow-Headers': 'Content-Type'
                      })
        
        return response
    
    def generate(self):
        # First, yield a heartbeat to establish the connection
        yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
        
        # Process thoughts from the queue
        while True:
            try:
                thought = self.thought_queue.get(timeout=1.0)

                if thought == "DONE":
                    break

                yield f"data: {thought}\n\n"
            except queue.Empty:
                # Send a heartbeat to keep the connection alive
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                continue

    def get(self, **kwargs):
        """
        Handle GET requests (legacy support)
        """
        return self._answer_stream_response(**kwargs)

    def post(self, **kwargs):
        """
        Handle POST requests with the new payload structure
        """
        return self._answer_stream_response(**kwargs)

    def options(self, **kwargs):
        """
        Handle OPTIONS requests for CORS
        """
        return self._answer_stream_response(**kwargs)


    # Override the callback handler in sales_analytics_assistant to forward thoughts to our queue
    def global_callback_handler(self, **kwargs):

        if "data" in kwargs:
            # Stream the model's thinking process
            thought_data = {
                "type": "thinking",
                "content": kwargs['data']
            }
            self.thought_queue.put(json.dumps(thought_data))
            
        elif "current_tool_use" in kwargs and kwargs["current_tool_use"].get("name"):
            # Stream tool usage information
            tool_data = {
                "type": "tool_use",
                "tool": kwargs['current_tool_use']['name']
            }
            self.thought_queue.put(json.dumps(tool_data))
            
        return None
        
    # Start a thread to process the agent's response
    def process_agent_response(self, user_input, model_id, thread_id, user="Deepesh"):
        #try:
        # Handle thread management
        chat_thread = None
        
        # Define the orchestrator system prompt
        MAIN_SYSTEM_PROMPT = f"""
        You are an assistant that routes queries to specialized agents:
            - For WAF questions → Use the waf_logs_assistant tool
            - For my personal task management → Use the personal_assistant tool
            - For Payment and Sales analytics → Use the sales_analytics_assistant tool
            - For specialized tasks -> Use mcp_servers_assistant tool
            - For simple questions, creative tasks, general knowledge that do not require specialized knowledge → Answer directly

            Rules:
            - Always select the most appropriate tool based on the user's query
            - In your final response, DO NOT include commentry for tool use

            
        """
        chat_thread = self.chat_history_repo.get_thread_by_id(thread_id, user)
        print(chat_thread)
        if (len(chat_thread['ui_msgs']) < 1):
            chat_thread['thread_title'] = user_input
        
        
        chat_thread_helper = ChatThreadHelper(chat_thread)
        model = BedrockModel(model_id=model_id, 
                                verbose=True, 
                                temperature=0.3)
        
        # Set up the orchestrator with the enhanced callback
        orchestrator = Agent(
            system_prompt=MAIN_SYSTEM_PROMPT,
            model=model,
            
            tools=[
                self.fintech_sales_agent.sales_analytics_assistant_tool(),
                    self.personal_tasks_manager.personal_task_manager_tool(),
                    self.mcp_servers_agent.mcp_servers_tool(),
                    self.waf_logs_agent.was_tool()],
            callback_handler=self.global_callback_handler,
            messages = chat_thread['agent_msgs']
        )
        
        # Process the user input
        response = orchestrator(user_input)
        
        # Get the final response and any query results
        last_message = orchestrator.messages[-2]['content']
        # print(f'\n\nmessages -->{orchestrator.messages}')
        final_response = ""
        query_results = []
        show_graph = False
        
        # Check if the response is a JSON string that might contain query results
        try:
            print(f'\n\nresponse--> {response}')
            response_json = json.loads(response)
            if isinstance(response_json, dict):
                if 'response' in response_json:
                    final_response = response_json['response']

                # if 'query_results' in response_json and isinstance(response_json['query_results'], list):
                #     query_results = response_json['query_results']
                # if 'show_graph' in response_json:
                #     show_graph = bool(response_json['show_graph'])
        except (json.JSONDecodeError, TypeError):
            # If not valid JSON or not a dict, use the response as is
            print('exception occurred')
            pass
        
        # If we couldn't extract from JSON, use the standard extraction
        if not final_response:
            for item in last_message:
                if 'text' in item: # direct LLM call, no tools involved
                    final_response = orchestrator.messages[-1]['content'][0]['text']
                elif 'toolResult' in item: # when results are coming from tools
                    final_response  = item['toolResult']['content'][0]['text']
                    try:
                        response_json   = json.loads(final_response)
                        final_response  = response_json['response']
                        query_results   = response_json['query_results']
                        show_graph      = response_json['show_graph']
                    except ValueError as ex:
                        response_json   = final_response
                        query_results   = []
                        show_graph      = False
                        

                    
    
        # Save the updated thread to the database
        # try:
        # attach tool messages from the agent
        chat_thread_helper.update_agent_messages(orchestrator.messages)
        
        chat_thread_helper.update_ui_messages(response=final_response,
                                                user_input=user_input,
                                                query_results=query_results,
                                                show_graph=show_graph)
        

        self.chat_history_repo.save_thread(chat_thread_helper.get_chat_thread(), is_new=False)
        

        logger.info(f"Saved chat thread {chat_thread['thread_id']} to database")
        # except Exception as e:
        #     logger.error(f"Failed to save chat thread to database: {str(e)}")
        
        # Send the final response with any query results and thread_id
        # final_data = {
        #     'type': 'final', 
        #     'content': final_response,
        #     'thread_id': chat_thread['thread_id']
        # }


        chat_thread = chat_thread_helper.get_chat_thread()
        final_data = {
            "thread_id": chat_thread['thread_id'],
            "type": "final",
            "ui_msgs": chat_thread['ui_msgs'],
            "status": "success"
        }
        
        self.thought_queue.put(json.dumps(final_data))

        # Calculate and log execution time
        end_time = time.time()
        execution_time = end_time - self.start_time
        self.util.log_data(f"Total execution time: {execution_time:.2f} seconds")
        
        # Signal that we're done
        self.thought_queue.put("DONE")
            
            
        # except Exception as e:
        #     # Handle any exceptions
        #     error_data = {
        #         'type': 'error',
        #         'content': f"Error processing request: {str(e)}"
        #     }
        #     self.thought_queue.put(json.dumps(error_data))
        #     self.thought_queue.put("DONE")
        #     logger.error(f"Error in process_agent_response: {str(e)}", exc_info=True)
        #     raise e

    