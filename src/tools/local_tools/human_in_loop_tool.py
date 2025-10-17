from langchain.tools import StructuredTool

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
    print("\n" + "="*70)
    print("🤖 AGENT REQUESTING PERMISSION")
    print("="*70)
    print(f"\n{operation_details}\n")
    print("="*70)
    
    response = input("Do you approve this operation?: ").strip().lower()
    
    return response


# Easy integration function
def get_approval_tool():
    approval_tool = StructuredTool.from_function(
        func=request_human_approval,
        name="request_approval",
        description=(
            """
            Request human approval before performing sensitive operations.
            
            The agent MUST call this tool before executing any file operations, data modifications, Creating stories,
            updating tasks, any changes in Azure DevOps, or other sensitive actions. 
            The agent should explain what it wants to do and why.
            
            Args:
                operation_details: A clear explanation of what operation the agent wants to perform,
                                why it's needed, and what the expected outcome is.
                Example: "I want to create a file named 'test.txt' with content 
                'Hello World' because you asked me to create a test file."
            
            Returns:
                str: Approval or rejection from the human user.
            """
        ),
    )
    return approval_tool