from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
import os
from langchain_openai import ChatOpenAI
from prompts.prompts import PRODUCT_OWNER, SCRUM_LEAD, PEER_REVIEWER, ROLE_PROMPT, Role_selection_prompt, json_creation_prompt
import json
from langchain.agents import AgentExecutor
from src.toolkits.toolkit import get_azdo_tool_kit, get_local_tool_kit
from langchain.agents import create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.callbacks import get_openai_callback
import asyncio
from src.utils.json_processor import extract_json_from_markdown
from src.utils.livefile_callbackandler import LiveFileCallbackHandler
from langchain_core.callbacks import FileCallbackHandler
from src.utils.uuid_generator import generate_uuid

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Initialize the language model
llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=OPENAI_API_KEY)

def _sync_append_cost(content: str, path: str = "cost_details.txt"):
    """Synchronous helper to append cost details to a file.

    Separated out so it can be executed via asyncio.to_thread without
    invoking open() inside an async function (avoids lint warnings).
    """
    with open(path, "a", encoding="utf-8") as f:
        f.write(content)

def get_role_based_prompt(user_input: str, role: str = None) -> str:
    """Returns the system prompt based on the selected role."""

    if role:
        selected_role = role
    else:
        role_prompt = Role_selection_prompt + "\n\nUser Input:\n{input}"
        input_prompt = role_prompt.format(input=user_input)
        response = llm.invoke(input_prompt)
        role_json = extract_json_from_markdown(response.content)

        if isinstance(role_json, dict) and "Role" in role_json:
            selected_role = role_json["Role"]
        print(f"Selected Role: {selected_role}")

    if selected_role.strip().lower() == "product owner":
        role_prompt = PRODUCT_OWNER
        print("Product Owner Agent Started...")
    elif selected_role.strip().lower() == "scrum lead":
        role_prompt = SCRUM_LEAD
        print("Scrum Lead Agent Started...")
    elif selected_role.strip().lower() == "peer review":
        role_prompt = PEER_REVIEWER
        print("Peer Reviewer Agent Started...")
    else:
        role_prompt = "Invalid role selected. Please choose a valid role."
    
    return role_prompt

async def rea_agent(user_prompt: str, role: str = None):
    """Sets up and returns an REA agent executor with Azure DevOps and local file operation tools."""
    print("Setting up REA agent...")
    uuid = generate_uuid()
    
    # Get tools
    azdo_tools = get_azdo_tool_kit()
    local_tools = get_local_tool_kit()
    all_tools = azdo_tools + local_tools
    
    print(f"Total tools available: {len(all_tools)}")

    # Get system prompt based on role
    system_prompt = get_role_based_prompt(user_prompt, role)

    # Additional instructions
    # additional_instructions = """
    # **IMPORTANT INSTRUCTIONS**:
    #     1. **CRITICAL**: Always use the 'human_input' tool to get human inputs/approval/suggestions.  
    #     2. If you are getting any errors while performing any operations, use the 'human_input' tool to get clarification or more information from the user before proceeding.
    #     3. Never end the conversation without confirming with the user using the 'human_input' tool.
    # """
    
    prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

    agent = create_openai_functions_agent(llm, all_tools, prompt)
    
    # Use it with your agent
    log_path = f"{role or 'no_role'}_agent_log_{uuid}.txt"
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"\n\n{'-'*20}\n{role or 'No Role Specified'} Agent started at {datetime.now().isoformat()}\n{'-'*20}\n")
        log_file.flush()

    handler = LiveFileCallbackHandler(log_path)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=all_tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=30,
        return_intermediate_steps=True,
        callbacks=[handler]
    )




    try:
        cost_details = ""
        with get_openai_callback() as cb:
            result = await agent_executor.ainvoke({"input": user_prompt})

            # with FileCallbackHandler("agent_output.log", mode='a') as handler:
            #     result = agent_executor.invoke(
            #         {"input": user_prompt},
            #         config={"callbacks": [handler]}
            #     )

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

            with open(log_path, "r", encoding="utf-8") as log_file:
                agent_logs = log_file.read()

            llm_response = llm.invoke(
                json_creation_prompt.format(agent_logs=agent_logs)
            )
            output_json = extract_json_from_markdown(llm_response.content)
            first_keys = {
                "Run_ID": uuid,
            }
            output_json = {**first_keys, **output_json}
            
            with open(f"{role or 'no_role'}_agent_output_{uuid}.json", "w", encoding="utf-8") as output_file:
                json.dump(output_json, output_file, indent=4)

            print("\nCost Details:")
            print(cost_details)
            return result
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()