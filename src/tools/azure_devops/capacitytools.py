import os
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv
from langchain.tools import Tool
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from azure.devops.v7_0.work.models import TeamContext
import time

load_dotenv()

# Configuration
organization_url = os.getenv('AZURE_ORG_URL', 'https://dev.azure.com/yourorg')
personal_access_token = os.getenv('AZURE_DEVOPS_PERSONAL_ACCESS_TOKEN', 'your-pat-token')
project_name = os.getenv('PROJECT_NAME', 'YourProject')


class AzureDevOpsTeamCapacityConnector:
    """Azure DevOps Team Members and Capacity Connector using PAT authentication"""
    
    def __init__(self, organization_url: str, personal_access_token: str, project_name: str):
        self.organization_url = organization_url
        self.project_name = project_name
        credentials = BasicAuthentication('', personal_access_token)
        self.connection = Connection(base_url=organization_url, creds=credentials)
        self.work_client = self.connection.clients.get_work_client()
        self.core_client = self.connection.clients.get_core_client()
    
    def get_team_members(self, team_name: str) -> str:
        """
        Get the list of team members for a specific team
        
        Args:
            team_name: Name of the team
            
        Returns:
            Formatted string with team member details
        """
        try:
            # Get team members
            time.sleep(5)  # To avoid rate limiting
            team_members = self.core_client.get_team_members_with_extended_properties(
                project_id=self.project_name,
                team_id=team_name
            )
            
            if not team_members:
                return f"No team members found for team '{team_name}'"
            
            result = f"Team Members for '{team_name}' ({len(team_members)} members):\n\n"
            
            for member in team_members:
                result += f"Name: {member.identity.display_name}\n"
                result += f"Unique Name: {member.identity.unique_name}\n"
                result += f"ID: {member.identity.id}\n"
                result += f"Email: {member.identity.unique_name}\n"
                
                # Check if member is team admin
                if hasattr(member, 'is_team_admin'):
                    result += f"Team Admin: {member.is_team_admin}\n"
                
                result += "---\n"
            
            return result
            
        except Exception as e:
            return f"Error retrieving team members: {str(e)}"
    
    def get_iteration_id(self, team_name: str, iteration_name: str) -> Optional[str]:
        """
        Get iteration ID (GUID) from iteration name
        
        Args:
            team_name: Name of the team
            iteration_name: Name of the iteration (e.g., 'Sprint 1')
            
        Returns:
            Iteration GUID or None if not found
        """
        try:
            time.sleep(5)  # To avoid rate limiting
            team_context = TeamContext(project=self.project_name, team=team_name)
            
            # Get all iterations for the team
            iterations = self.work_client.get_team_iterations(team_context=team_context)
            
            # Find the iteration by name
            for iteration in iterations:
                if iteration.name == iteration_name:
                    return iteration.id
            
            return None
            
        except Exception as e:
            raise Exception(f"Error retrieving iteration ID: {str(e)}")


    def get_team_capacity_for_iteration(self, team_name: str, iteration_name: str) -> str:
        """
        Get team member capacities for a specific iteration/sprint
        
        Args:
            team_name: Name of the team
            iteration_name: Name of the iteration (e.g., 'Sprint 1')
            
        Returns:
            Formatted string with capacity details for each team member
        """
        try:
            time.sleep(5)  # To avoid rate limiting
            # First, get the iteration GUID from the name
            iteration_id = self.get_iteration_id(team_name, iteration_name)
            
            if not iteration_id:
                # Try to list available iterations to help the user
                team_context = TeamContext(project=self.project_name, team=team_name)
                iterations = self.work_client.get_team_iterations(team_context=team_context)
                available = ', '.join([f"'{it.name}'" for it in iterations])
                return (f"Iteration '{iteration_name}' not found for team '{team_name}'. "
                    f"Available iterations: {available}")
            
            team_context = TeamContext(project=self.project_name, team=team_name)
            print(iteration_id)
            # Use the GUID to get capacities
            team_capacity = self.work_client.get_capacities_with_identity_ref_and_totals(
                team_context=team_context,
                iteration_id=iteration_id
            )
            print(team_capacity)
            if not team_capacity or not team_capacity.team_members:
                return f"No capacity information found for team '{team_name}' in iteration '{iteration_name}'"
            
            result = f"Team Capacity for '{team_name}' - Iteration '{iteration_name}':\n\n"
            
            for capacity in team_capacity.team_members:
                team_member = capacity.team_member
                
                result += f"Member: {team_member.display_name}\n"
                result += f"ID: {team_member.id}\n"
                
                # Get activities and capacity per day
                if capacity.activities:
                    result += f"Activities:\n"
                    for activity in capacity.activities:
                        result += f"  - {activity.name}: {activity.capacity_per_day} hours/day\n"
                
                # Get days off
                if capacity.days_off:
                    result += f"Days Off ({len(capacity.days_off)} days):\n"
                    for day_off in capacity.days_off:
                        result += f"  - Start: {day_off.start}, End: {day_off.end}\n"
                else:
                    result += "Days Off: None\n"
                
                result += "---\n"
            
            # Add summary from the totals
            result += f"\nSummary:\n"
            result += f"Total Team Members: {len(team_capacity.team_members)}\n"
            
            if hasattr(team_capacity, 'total_capacity_per_day'):
                result += f"Total Capacity per Day: {team_capacity.total_capacity_per_day} hours\n"
            if hasattr(team_capacity, 'total_days_off'):
                result += f"Total Days Off: {team_capacity.total_days_off} days\n"
            
            return result
            
        except Exception as e:
            return f"Error retrieving team capacity: {str(e)}"




def create_team_capacity_tools(
    organization_url: str = organization_url,
    personal_access_token: str = personal_access_token,
    project_name: str = project_name
) -> List[Tool]:
    """
    Create LangChain tools for Azure DevOps Team Members and Capacity operations
    
    Returns:
        List of LangChain Tool objects
    """
    connector = AzureDevOpsTeamCapacityConnector(
        organization_url=organization_url,
        personal_access_token=personal_access_token,
        project_name=project_name
    )
    
    tools = [
        Tool(
            name="work_get_team_members",
            func=lambda team_name: connector.get_team_members(team_name),
            description=(
                "Get the list of team members for a specific team in Azure DevOps. "
                "Input should be the team name (string). "
                "Returns member names, IDs, emails, and admin status. "
                "Example: \"Team Alpha\" or \"Development Team\""
            )
        ),
        
        Tool(
            name="work_get_team_capacity_for_iteration",
            func=lambda input_str: connector.get_team_capacity_for_iteration(
                **eval(input_str)
            ),
            description=(
                "Get team member capacities for a specific iteration/sprint. "
                "CRITICAL: Input must be a dictionary string in this EXACT format: "
                "{'team_name': '<team_name>', 'iteration_name': '<iteration_name>'} "
                "Replace <team_name> with the actual team name and <iteration_name> with sprint name. "
                "CORRECT example: {'team_name': 'aimetlab Team', 'iteration_name': 'Sprint 1'} "
                "WRONG: Just passing team name without dict structure will fail. "
                "Returns: capacity hours/day, activities, and days off for all team members."
            )
        ),
    ]
    
    return tools


# Example usage
# if __name__ == "__main__":
#     # Create the tools
#     tools = create_team_capacity_tools()
    
#     # Example 1: Get team members
#     print("\n=== Example 1: Getting team members ===")
#     team_members_tool = next(t for t in tools if t.name == "work_get_team_members")
#     # result = team_members_tool.run("aimetlab Team")
#     # print(result)
    
#     # Example 2: Get team capacity for an iteration
#     print("\n=== Example 2: Getting team capacity ===")
#     capacity_tool = next(t for t in tools if t.name == "work_get_team_capacity_for_iteration")
#     result = capacity_tool.run("{'team_name': 'aimetlab Team', 'iteration_name': 'Sprint 1'}")
#     print(result)