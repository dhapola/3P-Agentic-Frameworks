
import sys
from utils.utility import Utility
from utils.utility import Utility
from providers.mcp_provider import MCPProvider
from strands import Agent, tool
from strands.models import BedrockModel
from agents.agent_callback_handler import common_agent_callback_handler

model_id = 'apac.amazon.nova-lite-v1:0'


class PersonalTasksAgent():

    def __init__(self, thought_queue):
        self.util = Utility()
        self.thought_queue = thought_queue

    def agent_callback_handler(self, **kwargs):
        common_agent_callback_handler(thought_queue=self.thought_queue, **kwargs)


    def personal_task_manager_tool(self):

        @tool 
        def quip_tasks_assistant(user_input: str):
            '''
            This tool performs personal task management actions like retrieving outstanding tasks, all tasks, marking tasks complete.

            Args:
                user_input (str): action requested by user
                
            Returns:
                dict: a dictionary containing answer
            '''

            SYSTEM_PROMPT ="""
                    You are personal task assistant. Use tools to manage tasks. Provide your response in markdown format. Task list should be numbered.
                    """
            
            mcp_tools = MCPProvider().get_tools_for_mcp_server('d2-quip-mcp-server')

            model = BedrockModel(model_id=model_id, verbose=True)
            agent = Agent(
                system_prompt=SYSTEM_PROMPT,
                model=model,
                tools=mcp_tools,
                callback_handler=self.agent_callback_handler
            )

            #self.util.log_data('calling quip task agent')
            response = agent(user_input)
            content = str(response)
            #self.util.log_data(f'\n\nquip task response  ==> {content}\n\n')
            return content
        
        return quip_tasks_assistant