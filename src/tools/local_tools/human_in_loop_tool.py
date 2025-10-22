from langchain.tools import StructuredTool
import time

def request_human_approval(operation_details: str) -> str:
    """
    Request human approval before performing sensitive operations.
    
    The agent MUST call this tool before executing any file operations, data modifications,
    or other sensitive actions. The agent should explain what it wants to do and why.
    
    Args:
        operation_details: A clear explanation of what operation the agent wants to perform,
                          why it's needed, and what the expected outcome is.
                          Example: "I want to create a file named 'test.txt' with content 
                          'Hello World' because you asked me to create a test file."
    
    Returns:
        str: "APPROVED" if user approves, "REJECTED" if user rejects with reason
    """
    time.sleep(5)  # To avoid rate limiting
    print("\n" + "="*70)
    print("🤖 AGENT QUESTION")
    print("="*70)
    print(f"\n{operation_details}\n")
    print("="*70)

    response = input("Your Input: ").strip().lower()

    return response


# Easy integration function
def get_approval_tool():
    approval_tool = StructuredTool.from_function(
        func=request_human_approval,
        name="human_input",
        description=(
            """
            Request human approval/inputs or when there are so many options available before performing sensitive operations.
            **CRITICAL**:
            The agent MUST call this tool for all of the following scenarios:
            - Before executing any 
                - file operations
                - data modifications
                - Creating/Updating stories/tasks/epics
                - All changes in Azure DevOps
            - Want to get the user input or suggestion
            - Whenever you face any errors
                - Get clarification
                - More information
            - Other sensitive actions.
            - Everytime before ending the conversation.
            The agent should explain what it wants and why.
            
            Args:
                operation_details: A clear explanation of what operation the agent wants to perform,
                                why it's needed, and what the expected outcome is.
                Example 1: "I want to create a file named 'test.txt' with content 'Hello World' because you asked me to create a test file."
                Example 2: "These are multiple user stories available, which one should I prioritize?"
                Example 3: "I want to update the task 'Implement feature X' with new details because the requirements have changed."
            
            Returns:
                str: Approval or rejection from the human user.
            """
        ),
    )
    return approval_tool