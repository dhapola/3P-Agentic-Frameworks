import ast
import json
import re
from datetime import date
from utils.utility import Utility
from utils.utility import Utility, GREEN_COLOR, RESET_COLOR, WHITE_COLOR, BLUE_COLOR
from providers.mcp_provider import MCPProvider
from agents.agent_callback_handler import common_agent_callback_handler
from strands import Agent, tool
from strands.models import BedrockModel
from utils.tool_message_schema import MessageSchema
from decimal import Decimal

task_manager_model_id = 'apac.anthropic.claude-3-haiku-20240307-v1:0' #'apac.anthropic.claude-3-7-sonnet-20250219-v1:0'
sql_generator_model_id  = 'apac.anthropic.claude-3-5-sonnet-20241022-v2:0'
#response_generator_model_id = 'apac.amazon.nova-lite-v1:0'


# Define the system prompt as a global variable
# SYSTEM_PROMPT = f"""
#         You are an agent designed to answer questions by finding data from payment database. Your workflow is as follows:
#         1. Understand the User Query:
#         - Carefully read and interpret the user's question, which will always be provided in natural language.
#         2. Table Schema Retrieval -> get the tables from the database and identify appropriate table having data for answering the question
#         - Sample query to retrieve table schema: SELECT column_name, data_type, character_maximum_length FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '<table_name>';
#         3. Generate PostgreSQL compatible query to retrieve data from the tables
#         4. Execute the generated SQL query in the database
#         5. Retrieve the results, handle any errors or ambiguities gracefully.

#         Key Responsibilities:
#         - Accurately interpret diverse natural language questions.
#         - Reliably map questions to the correct database tables and fields.
#         - Summarize and explain results in user-friendly language.

#         Decision Protocol:
#         - If the question is unclear, ask the user for clarification before proceeding.
#         - If multiple tables or joins are needed, construct the appropriate SQL statements.
#         - Always prioritize data privacy and query efficiency.

#         Available Tables:
#         - daily_sales_report - use this table for daily, monthly, quarterly and yearly sales data
#         - transactions - use this table for real time transaction information
#         - payment_methods - use this table to find payment methods
#         - payment_gateways - use this table to find payment gateways

#         Today's date is {date.today().strftime('%Y-%m-%d')}

#         use ₹ currency symbol when needed.
#         format numbers with commas as per Indian standards
        
#         """

SYSTEM_PROMPT = f"""
        You are a business analyst. you have been provided a postgresql database of payments. you need to answer questions from the data in db. Your workflow is as follows:
        1. Understand the question
        2. Table Schema Retrieval -> get the tables from the database and identify appropriate table having data for answering the question
        - Sample query to retrieve table schema: SELECT column_name, data_type, character_maximum_length FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '<table_name>';
        3. Generate PostgreSQL compatible SQL query to fetch data from the tables
        4. Execute the generated SQL query
        5. Retrieve the results, handle any errors or ambiguities gracefully.

        Decision Protocol:
        - If the question is unclear, ask the user for clarification before proceeding.
        - If multiple tables or joins are needed, construct the appropriate SQL statements.
        - Always prioritize data privacy and query efficiency.

        Available Tables:
        - daily_sales_report - use this table for daily, monthly, quarterly and yearly sales data
        - transactions - use this table for real time transaction information
        - payment_methods - use this table to find payment methods
        - payment_gateways - use this table to find payment gateways

        Today's date is {date.today().strftime('%Y-%m-%d')}

        use ₹ currency symbol when needed.
        format numbers with commas as per Indian standards
        
        """


class FintechSalesAgent():

    def __init__(self, thought_queue):
        self.util = Utility()
        self.thought_queue = thought_queue

    def agent_callback_handler(self, **kwargs):
        common_agent_callback_handler(thought_queue=self.thought_queue, **kwargs)
    

    def sales_analytics_assistant_tool(self):
        @tool 
        def sales_analytics_assistant(user_input: str) -> dict:
            """
            Use this tool for searching payment transactions and sales data
            
            Args:
                user_input (str): user's question
                
            Returns:
                dict: a dictionary containing natural language response & query results
            """
            

            mcp_tools = MCPProvider().get_tools_for_mcp_server('postgres-mcp-server')
            
            # Get the tools from the MCP server
            tools = mcp_tools

            # self.util.log_data(f'tools ==> {tools}')

            model = BedrockModel(model_id=task_manager_model_id, verbose=True, temperature=0.3)
            agent = Agent(
                system_prompt=SYSTEM_PROMPT,
                model=model,
                tools=tools,
                callback_handler=self.agent_callback_handler,
            )
            response = agent(user_input)

            query_results = agent.messages[-2]
            print(f'\nagent.messages -->{agent.messages}\n')
            query_results = query_results['content'][-1]['toolResult']['content'][0]['text']
            print(f'\nquery_results -->{query_results}\n')

            query_results = re.sub(r"Decimal\('([0-9.]+)'\)", r"\1", query_results)
            query_results = ast.literal_eval(query_results)
            query_results = json.dumps(query_results)
            
            show_graph = len(query_results)>1
            
            return json.dumps(MessageSchema.create(response=str(response), query_results=query_results, show_graph=show_graph))
        return sales_analytics_assistant

