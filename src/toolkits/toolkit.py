import os
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

from src.tools.azure_devops.workitemtools import create_azdo_work_items_tools
from src.tools.azure_devops.repositrytools import create_azdo_repositories_tools
from src.tools.azure_devops.pipelinetools import create_azdo_pipelines_tools
from src.tools.azure_devops.misctools import create_azdo_additional_services_tools
from src.tools.local_tools.editor_tools import get_writer_tool, get_file_lister_tool, get_reader_tool
from src.tools.local_tools.human_in_loop_tool import get_approval_tool
from src.tools.azure_devops.capacitytools import create_team_capacity_tools


# Configuration
organization_url = os.getenv('AZURE_ORG_URL', 'https://dev.azure.com/yourorg')
personal_access_token = os.getenv('AZURE_DEVOPS_PERSONAL_ACCESS_TOKEN', 'your-pat-token')
project_name = os.getenv('PROJECT_NAME', 'YourProject')


def get_azdo_tool_kit():
    """Returns a list of Azure DevOps tools and local file operation tools."""
    tools = []

    # Add Azure DevOps tools
    tools.extend(create_azdo_work_items_tools(organization_url, personal_access_token, project_name))
    tools.extend(create_azdo_repositories_tools(organization_url, personal_access_token, project_name))
    tools.extend(create_azdo_pipelines_tools(organization_url, personal_access_token, project_name))
    tools.extend(create_azdo_additional_services_tools(organization_url, personal_access_token, project_name))
    tools.extend(create_team_capacity_tools(organization_url, personal_access_token, project_name))
    return tools

def get_local_tool_kit(folders_to_omit: Optional[list] = None):
    """Returns a list of local file operation tools."""
    
    if folders_to_omit is None:
        folders_to_omit = ["node_modules", ".git", "__pycache__", "venv", ".venv", "env", ".env","dump"]
    tools = [
        get_writer_tool(),
        get_reader_tool(),
        get_file_lister_tool(folders_to_omit),
        get_approval_tool()
    ]
    return tools