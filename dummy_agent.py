from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
import os
from langchain_openai import ChatOpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

from prompt.prompts import system_prompt
from src.tools.playwright_tools import create_langchain_tool
from mcp_registry import ServerRegistry, MCPAggregator, get_config_path
import json
from langchain.agents import AgentExecutor
from src.tools.editor_tools import get_writer_tool
from src.tools.get_user_story_tool import create_work_items_tool
from langchain_community.callbacks import get_openai_callback

# We'll discover MCP servers via the registry and use an aggregator per run.


def _sync_append_cost(content: str, path: str = "cost_details.txt"):
    """Synchronous helper to append cost details to a file.

    Separated out so it can be executed via asyncio.to_thread without
    invoking open() inside an async function (avoids lint warnings).
    """
    with open(path, "a", encoding="utf-8") as f:
        f.write(content)

async def run_agent_task(agent_executor, task: str):
    """Run an agent task asynchronously"""
    result = await agent_executor.ainvoke({"input": task})
    return result

async def test_agent(testing_prompt):
    # Connect to MCP registry and aggregator
    print("Connecting to MCP registry and aggregators...")
    registry = ServerRegistry.from_config(get_config_path())

    async with MCPAggregator(registry) as aggregator:
        # Discover tools via aggregator
        results = await aggregator.list_tools()
        mcp_tools = [
            {"name": t.name, "description": t.description or "", "schema": t.inputSchema or {}}
            for t in results.tools
        ]
        print(f"Found {len(mcp_tools)} tools:")
        for tool in mcp_tools:
            print(f"  - {tool['name']}: {tool['description']}")

        # Adapter to match existing PlaywrightMCPClient.call_tool shape
        class AggregatorClient:
            def __init__(self, aggregator):
                self.aggregator = aggregator

            async def call_tool(self, tool_name: str, arguments: dict) -> str:
                res = await self.aggregator.call_tool(tool_name, arguments)
                # Try to convert MCP return items to JSON similar to Playwright client
                try:
                    return json.dumps([item.model_dump() for item in res.content])
                except Exception:
                    return json.dumps(res.content if hasattr(res, "content") else res)

        mcp_client = AggregatorClient(aggregator)

        # Convert MCP tools to LangChain tools
        langchain_tools = [create_langchain_tool(tool, mcp_client) for tool in mcp_tools]
        editor_tool = [get_writer_tool()]
        azdo_tool = [create_work_items_tool()]

        # Initialize LLM - Use ChatOpenAI with proper configuration
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,
            openai_api_key=OPENAI_API_KEY
        )

        # Use the OpenAI Functions agent instead of structured chat
        from langchain.agents import create_openai_functions_agent
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_openai_functions_agent(llm, langchain_tools+editor_tool, prompt)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=langchain_tools+editor_tool,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=20,
            return_intermediate_steps=True
        )

        try:
            cost_details = ""
            with get_openai_callback() as cb:
                result = await agent_executor.ainvoke({"input": testing_prompt})
                cost_details += f"""
                {"-"*20}
                Agent execution time: {datetime.now().isoformat()}
                Total Tokens: {cb.total_tokens}
                Prompt Tokens: {cb.prompt_tokens}
                Completion Tokens: {cb.completion_tokens}
                Total Cost (USD): ${cb.total_cost}
                {"-"*20}
                """
                # Use asyncio.to_thread for file I/O inside async function
                import asyncio as _asyncio
                await _asyncio.to_thread(_sync_append_cost, cost_details, "cost_details.txt")
                print("\nResult:", result.get("output", result))
                print("\nCost Details:")
                print(cost_details)
                return result
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        # aggregator context will automatically clean up connections

import asyncio
from prompt.prompts import testcases_prompt
import json

with open("prerequsites/credentials.json", "r", encoding="utf-8") as f:
    credentials = json.load(f)

task_id = "3"
testcases_prompt = testcases_prompt.format(
    task_id=task_id,
    credentials=credentials,
)
response = asyncio.run(test_agent(testcases_prompt))