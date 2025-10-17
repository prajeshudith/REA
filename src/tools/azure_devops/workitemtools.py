import os
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv
from langchain.tools import Tool
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from azure.devops.v7_0.work_item_tracking.models import (
    Wiql, 
    JsonPatchOperation,
    WorkItemRelation,
    WorkItemRelationUpdates,
    CommentCreate
)
from azure.devops.v7_0.work.models import TeamContext
import json

load_dotenv()

# Configuration
organization_url = os.getenv('AZURE_ORG_URL', 'https://dev.azure.com/yourorg')
personal_access_token = os.getenv('AZURE_DEVOPS_PERSONAL_ACCESS_TOKEN', 'your-pat-token')
project_name = os.getenv('PROJECT_NAME', 'YourProject')


class AzureDevOpsWorkItemsConnector:
    """Azure DevOps Work Items Connector using PAT authentication"""
    
    def __init__(self, organization_url: str, personal_access_token: str, project_name: str):
        self.organization_url = organization_url
        self.project_name = project_name
        credentials = BasicAuthentication('', personal_access_token)
        self.connection = Connection(base_url=organization_url, creds=credentials)
        self.wit_client = self.connection.clients.get_work_item_tracking_client()
        self.work_client = self.connection.clients.get_work_client()
    
    def my_work_items(self, max_results: int = 50) -> str:
        """Retrieve work items relevant to the authenticated user"""
        try:
            # Query for work items assigned to the current user
            wiql_query = f"""
            SELECT [System.Id], [System.Title], [System.State], 
                   [System.WorkItemType], [System.AssignedTo]
            FROM WorkItems
            WHERE [System.TeamProject] = '{self.project_name}'
            AND [System.AssignedTo] = @Me
            ORDER BY [System.ChangedDate] DESC
            """
            
            wiql = Wiql(query=wiql_query)
            query_results = self.wit_client.query_by_wiql(wiql, top=max_results).work_items
            
            if not query_results:
                return "No work items found assigned to you."
            
            work_item_ids = [item.id for item in query_results]
            work_items = self.wit_client.get_work_items(ids=work_item_ids, expand='Relations')
            
            result = f"Found {len(work_items)} work items assigned to you:\n\n"
            for item in work_items:
                fields = item.fields
                result += f"ID: {item.id}\n"
                result += f"Type: {fields.get('System.WorkItemType', '')}\n"
                result += f"Title: {fields.get('System.Title', '')}\n"
                result += f"State: {fields.get('System.State', '')}\n"
                result += f"URL: {item.url}\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error retrieving work items: {str(e)}"
    
    def get_work_item(self, work_item_id: int) -> str:
        """Get a single work item by ID"""
        try:
            work_item = self.wit_client.get_work_item(
                id=work_item_id,
                expand='All'
            )
            
            fields = work_item.fields
            result = f"Work Item Details (ID: {work_item_id})\n\n"
            result += f"Type: {fields.get('System.WorkItemType', '')}\n"
            result += f"Title: {fields.get('System.Title', '')}\n"
            result += f"State: {fields.get('System.State', '')}\n"
            result += f"Assigned To: {fields.get('System.AssignedTo', {}).get('displayName', 'Unassigned')}\n"
            result += f"Created Date: {fields.get('System.CreatedDate', '')}\n"
            result += f"Changed Date: {fields.get('System.ChangedDate', '')}\n"
            result += f"Description: {fields.get('System.Description', '')}\n"
            result += f"Tags: {fields.get('System.Tags', '')}\n"
            result += f"Priority: {fields.get('Microsoft.VSTS.Common.Priority', 'N/A')}\n"
            result += f"URL: {work_item.url}\n"
            
            # Include relations if any
            if work_item.relations:
                result += f"\nRelations ({len(work_item.relations)}):\n"
                for rel in work_item.relations:
                    result += f"  - {rel.rel}: {rel.url}\n"
            
            return result
        except Exception as e:
            return f"Error retrieving work item {work_item_id}: {str(e)}"
    
    def get_work_items_batch(self, work_item_ids: List[int]) -> str:
        """Retrieve multiple work items by IDs in batch"""
        try:
            if not work_item_ids:
                return "No work item IDs provided."
            
            work_items = self.wit_client.get_work_items(
                ids=work_item_ids,
                expand='Relations'
            )
            
            result = f"Retrieved {len(work_items)} work items:\n\n"
            for item in work_items:
                fields = item.fields
                result += f"ID: {item.id}\n"
                result += f"Type: {fields.get('System.WorkItemType', '')}\n"
                result += f"Title: {fields.get('System.Title', '')}\n"
                result += f"State: {fields.get('System.State', '')}\n"
                result += f"Assigned To: {fields.get('System.AssignedTo', {}).get('displayName', 'Unassigned')}\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error retrieving work items: {str(e)}"
    
    def create_work_item(self, work_item_type: str, title: str, 
                        description: str = "", assigned_to: str = "", 
                        tags: str = "", priority: int = 2) -> str:
        """Create a new work item"""
        try:
            document = []
            
            # Add title
            document.append(JsonPatchOperation(
                op="add",
                path="/fields/System.Title",
                value=title
            ))
            
            # Add description if provided
            if description:
                document.append(JsonPatchOperation(
                    op="add",
                    path="/fields/System.Description",
                    value=description
                ))
            
            # Add assigned to if provided
            if assigned_to:
                document.append(JsonPatchOperation(
                    op="add",
                    path="/fields/System.AssignedTo",
                    value=assigned_to
                ))
            
            # Add tags if provided
            if tags:
                document.append(JsonPatchOperation(
                    op="add",
                    path="/fields/System.Tags",
                    value=tags
                ))
            
            # Add priority
            document.append(JsonPatchOperation(
                op="add",
                path="/fields/Microsoft.VSTS.Common.Priority",
                value=priority
            ))
            
            work_item = self.wit_client.create_work_item(
                document=document,
                project=self.project_name,
                type=work_item_type
            )
            
            return f"Successfully created {work_item_type} with ID: {work_item.id}\nTitle: {title}\nURL: {work_item.url}"
        except Exception as e:
            return f"Error creating work item: {str(e)}"
    
    def update_work_item(self, work_item_id: int, updates: Dict[str, Any]) -> str:
        """Update a work item with specified fields"""
        try:
            document = []
            
            for field_path, value in updates.items():
                # Normalize field path
                if not field_path.startswith("/fields/"):
                    field_path = f"/fields/{field_path}"
                
                document.append(JsonPatchOperation(
                    op="add",
                    path=field_path,
                    value=value
                ))
            
            work_item = self.wit_client.update_work_item(
                document=document,
                id=work_item_id,
                project=self.project_name
            )
            
            return f"Successfully updated work item {work_item_id}\nURL: {work_item.url}"
        except Exception as e:
            return f"Error updating work item {work_item_id}: {str(e)}"
    
    def add_work_item_comment(self, work_item_id: int, comment_text: str) -> str:
        """Add a comment to a work item"""
        try:
            comment = CommentCreate(text=comment_text)
            result = self.wit_client.add_comment(
                project=self.project_name,
                work_item_id=work_item_id,
                comment=comment
            )
            
            return f"Successfully added comment to work item {work_item_id}\nComment ID: {result.id}"
        except Exception as e:
            return f"Error adding comment to work item {work_item_id}: {str(e)}"
    
    def list_work_item_comments(self, work_item_id: int) -> str:
        """Retrieve comments for a work item"""
        try:
            comments = self.wit_client.get_comments(
                project=self.project_name,
                work_item_id=work_item_id
            )
            
            if not comments.comments:
                return f"No comments found for work item {work_item_id}"
            
            result = f"Comments for work item {work_item_id} ({comments.total_count} total):\n\n"
            for comment in comments.comments:
                result += f"Comment ID: {comment.id}\n"
                result += f"Created By: {comment.created_by.display_name if comment.created_by else 'Unknown'}\n"
                result += f"Created Date: {comment.created_date}\n"
                result += f"Text: {comment.text}\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error retrieving comments for work item {work_item_id}: {str(e)}"
    
    def add_child_work_items(self, parent_id: int, work_item_type: str, 
                            titles: List[str]) -> str:
        """Create child work items for a parent work item"""
        try:
            results = []
            for title in titles:
                # Create the child work item
                document = [
                    JsonPatchOperation(
                        op="add",
                        path="/fields/System.Title",
                        value=title
                    )
                ]
                
                child_item = self.wit_client.create_work_item(
                    document=document,
                    project=self.project_name,
                    type=work_item_type
                )
                
                # Link to parent
                link_document = [
                    JsonPatchOperation(
                        op="add",
                        path="/relations/-",
                        value={
                            "rel": "System.LinkTypes.Hierarchy-Reverse",
                            "url": f"{self.organization_url}/{self.project_name}/_apis/wit/workItems/{parent_id}"
                        }
                    )
                ]
                
                self.wit_client.update_work_item(
                    document=link_document,
                    id=child_item.id,
                    project=self.project_name
                )
                
                results.append(f"Created {work_item_type} #{child_item.id}: {title}")
            
            return f"Successfully created {len(results)} child work items for parent #{parent_id}:\n" + "\n".join(results)
        except Exception as e:
            return f"Error creating child work items: {str(e)}"
    
    def link_work_items(self, source_id: int, target_id: int, 
                       link_type: str = "System.LinkTypes.Related") -> str:
        """Link two work items together"""
        try:
            document = [
                JsonPatchOperation(
                    op="add",
                    path="/relations/-",
                    value={
                        "rel": link_type,
                        "url": f"{self.organization_url}/{self.project_name}/_apis/wit/workItems/{target_id}"
                    }
                )
            ]
            
            work_item = self.wit_client.update_work_item(
                document=document,
                id=source_id,
                project=self.project_name
            )
            
            return f"Successfully linked work item #{source_id} to #{target_id} with link type: {link_type}"
        except Exception as e:
            return f"Error linking work items: {str(e)}"
    
    def get_work_items_for_iteration(self, team_name: str, iteration_path: str) -> str:
        """Retrieve work items for a specific iteration"""
        try:
            wiql_query = f"""
            SELECT [System.Id], [System.Title], [System.State], 
                   [System.WorkItemType], [System.AssignedTo]
            FROM WorkItems
            WHERE [System.TeamProject] = '{self.project_name}'
            AND [System.IterationPath] = '{iteration_path}'
            ORDER BY [System.WorkItemType], [System.State]
            """
            
            wiql = Wiql(query=wiql_query)
            query_results = self.wit_client.query_by_wiql(wiql).work_items
            
            if not query_results:
                return f"No work items found for iteration: {iteration_path}"
            
            work_item_ids = [item.id for item in query_results]
            work_items = self.wit_client.get_work_items(ids=work_item_ids)
            
            result = f"Work items in iteration '{iteration_path}' ({len(work_items)} total):\n\n"
            for item in work_items:
                fields = item.fields
                result += f"ID: {item.id} | Type: {fields.get('System.WorkItemType', '')} | "
                result += f"State: {fields.get('System.State', '')} | "
                result += f"Title: {fields.get('System.Title', '')}\n"
            
            return result
        except Exception as e:
            return f"Error retrieving work items for iteration: {str(e)}"
    
    def list_backlogs(self, team_name: str) -> str:
        """Retrieve backlogs for a team"""
        try:
            team_context = TeamContext(project=self.project_name, team=team_name)
            backlogs = self.work_client.get_backlogs(team_context)
            
            result = f"Backlogs for team '{team_name}':\n\n"
            for backlog in backlogs:
                result += f"Name: {backlog.name}\n"
                result += f"ID: {backlog.id}\n"
                result += f"Rank: {backlog.rank}\n"
                result += f"Type: {backlog.type}\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error retrieving backlogs: {str(e)}"
    
    def get_backlog_work_items(self, team_name: str, backlog_id: str) -> str:
        """Retrieve work items for a specific backlog"""
        try:
            team_context = TeamContext(project=self.project_name, team=team_name)
            backlog_items = self.work_client.get_backlog_level_work_items(
                team_context=team_context,
                backlog_id=backlog_id
            )
            
            if not backlog_items.work_items:
                return f"No work items found in backlog: {backlog_id}"
            
            work_item_ids = [item.target.id for item in backlog_items.work_items]
            work_items = self.wit_client.get_work_items(ids=work_item_ids)
            
            result = f"Work items in backlog '{backlog_id}' ({len(work_items)} total):\n\n"
            for item in work_items:
                fields = item.fields
                result += f"ID: {item.id}\n"
                result += f"Type: {fields.get('System.WorkItemType', '')}\n"
                result += f"Title: {fields.get('System.Title', '')}\n"
                result += f"State: {fields.get('System.State', '')}\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error retrieving backlog work items: {str(e)}"
    
    def query_work_items(self, wiql_query: str) -> str:
        """Execute a WIQL query to retrieve work items"""
        try:
            wiql = Wiql(query=wiql_query)
            query_results = self.wit_client.query_by_wiql(wiql).work_items
            
            if not query_results:
                return "No work items found matching the query."
            
            work_item_ids = [item.id for item in query_results]
            work_items = self.wit_client.get_work_items(ids=work_item_ids[:200])  # Limit to 200
            
            result = f"Query returned {len(work_items)} work items:\n\n"
            for item in work_items:
                fields = item.fields
                result += f"ID: {item.id} | Type: {fields.get('System.WorkItemType', '')} | "
                result += f"Title: {fields.get('System.Title', '')}\n"
            
            return result
        except Exception as e:
            return f"Error executing query: {str(e)}"
    
    def link_work_item_to_pull_request(self, work_item_id: int, pull_request_id: int, 
                                       repository_id: str) -> str:
        """Link a work item to a pull request"""
        try:
            # Construct the PR artifact URL
            pr_url = f"vstfs:///Git/PullRequestId/{self.project_name}%2F{repository_id}%2F{pull_request_id}"
            
            document = [
                JsonPatchOperation(
                    op="add",
                    path="/relations/-",
                    value={
                        "rel": "ArtifactLink",
                        "url": pr_url,
                        "attributes": {
                            "name": "Pull Request"
                        }
                    }
                )
            ]
            
            work_item = self.wit_client.update_work_item(
                document=document,
                id=work_item_id,
                project=self.project_name
            )
            
            return f"Successfully linked work item #{work_item_id} to Pull Request #{pull_request_id}"
        except Exception as e:
            return f"Error linking work item to pull request: {str(e)}"
    
    def get_work_item_type(self, work_item_type_name: str) -> str:
        """Get a specific work item type definition"""
        try:
            work_item_type = self.wit_client.get_work_item_type(
                project=self.project_name,
                type=work_item_type_name
            )
            
            result = f"Work Item Type: {work_item_type.name}\n\n"
            result += f"Description: {work_item_type.description}\n"
            result += f"Color: {work_item_type.color}\n"
            result += f"Icon: {work_item_type.icon}\n"
            result += f"Is Disabled: {work_item_type.is_disabled}\n\n"
            
            if work_item_type.fields:
                result += f"Fields ({len(work_item_type.fields)}):\n"
                for field in work_item_type.fields:
                    result += f"  - {field.name} ({field.reference_name}): {field.type}\n"
                    if field.help_text:
                        result += f"    Help: {field.help_text}\n"
            
            if work_item_type.states:
                result += f"\nStates: {', '.join(work_item_type.states)}\n"
            
            return result
        except Exception as e:
            return f"Error retrieving work item type: {str(e)}"
    
    def get_query(self, query_id_or_path: str) -> str:
        """Get a saved query by its ID or path"""
        try:
            # Try to get by ID first, then by path
            try:
                query = self.wit_client.get_query(
                    project=self.project_name,
                    query=query_id_or_path
                )
            except:
                # If ID fails, try as path
                query = self.wit_client.get_query(
                    project=self.project_name,
                    query=query_id_or_path,
                    depth=1
                )
            
            result = f"Query: {query.name}\n\n"
            result += f"ID: {query.id}\n"
            result += f"Path: {query.path}\n"
            result += f"Query Type: {query.query_type}\n"
            if query.wiql:
                result += f"\nWIQL:\n{query.wiql}\n"
            
            return result
        except Exception as e:
            return f"Error retrieving query: {str(e)}"
    
    def get_query_results_by_id(self, query_id: str) -> str:
        """Execute a saved query and retrieve results"""
        try:
            # Get the query first
            query = self.wit_client.get_query(
                project=self.project_name,
                query=query_id
            )
            
            # Execute the query
            wiql = Wiql(query=query.wiql)
            query_results = self.wit_client.query_by_wiql(wiql).work_items
            
            if not query_results:
                return f"Query '{query.name}' returned no work items."
            
            work_item_ids = [item.id for item in query_results]
            work_items = self.wit_client.get_work_items(ids=work_item_ids[:200])
            
            result = f"Results for query '{query.name}' ({len(work_items)} work items):\n\n"
            for item in work_items:
                fields = item.fields
                result += f"ID: {item.id} | Type: {fields.get('System.WorkItemType', '')} | "
                result += f"State: {fields.get('System.State', '')} | "
                result += f"Title: {fields.get('System.Title', '')}\n"
            
            return result
        except Exception as e:
            return f"Error executing query: {str(e)}"
    
    def update_work_items_batch(self, updates_list: List[Dict[str, Any]]) -> str:
        """Update multiple work items in batch"""
        try:
            results = []
            
            for update_item in updates_list:
                work_item_id = update_item['work_item_id']
                updates = update_item['updates']
                
                document = []
                for field_path, value in updates.items():
                    if not field_path.startswith("/fields/"):
                        field_path = f"/fields/{field_path}"
                    
                    document.append(JsonPatchOperation(
                        op="add",
                        path=field_path,
                        value=value
                    ))
                
                work_item = self.wit_client.update_work_item(
                    document=document,
                    id=work_item_id,
                    project=self.project_name
                )
                
                results.append(f"Updated work item #{work_item_id}")
            
            return f"Successfully updated {len(results)} work items:\n" + "\n".join(results)
        except Exception as e:
            return f"Error updating work items in batch: {str(e)}"
    
    def work_items_link_batch(self, links: List[Dict[str, Any]]) -> str:
        """Link multiple work items together in batch"""
        try:
            results = []
            
            for link in links:
                source_id = link['source_id']
                target_id = link['target_id']
                link_type = link.get('link_type', 'System.LinkTypes.Related')
                
                document = [
                    JsonPatchOperation(
                        op="add",
                        path="/relations/-",
                        value={
                            "rel": link_type,
                            "url": f"{self.organization_url}/{self.project_name}/_apis/wit/workItems/{target_id}"
                        }
                    )
                ]
                
                self.wit_client.update_work_item(
                    document=document,
                    id=source_id,
                    project=self.project_name
                )
                
                results.append(f"Linked #{source_id} -> #{target_id} ({link_type})")
            
            return f"Successfully created {len(results)} links:\n" + "\n".join(results)
        except Exception as e:
            return f"Error linking work items in batch: {str(e)}"
    
    def work_item_unlink(self, work_item_id: int, link_indices: List[int]) -> str:
        """Unlink one or many links from a work item"""
        try:
            # First get the work item to see its relations
            work_item = self.wit_client.get_work_item(
                id=work_item_id,
                expand='Relations'
            )
            
            if not work_item.relations:
                return f"Work item #{work_item_id} has no relations to unlink."
            
            # Create remove operations for specified indices
            document = []
            for index in sorted(link_indices, reverse=True):  # Remove from end to preserve indices
                if index < len(work_item.relations):
                    document.append(JsonPatchOperation(
                        op="remove",
                        path=f"/relations/{index}"
                    ))
            
            if not document:
                return f"No valid link indices found to remove."
            
            updated_item = self.wit_client.update_work_item(
                document=document,
                id=work_item_id,
                project=self.project_name
            )
            
            return f"Successfully removed {len(document)} link(s) from work item #{work_item_id}"
        except Exception as e:
            return f"Error unlinking work item relations: {str(e)}"
    
    def add_artifact_link(self, work_item_id: int, artifact_type: str, 
                         artifact_id: str, artifact_name: str = "") -> str:
        """Link to artifacts like branch, pull request, commit, and build"""
        try:
            # Construct artifact URL based on type
            artifact_urls = {
                "branch": f"vstfs:///Git/Ref/{self.project_name}%2F{artifact_id}",
                "pullrequest": f"vstfs:///Git/PullRequestId/{self.project_name}%2F{artifact_id}",
                "commit": f"vstfs:///Git/Commit/{self.project_name}%2F{artifact_id}",
                "build": f"vstfs:///Build/Build/{artifact_id}"
            }
            
            artifact_type_lower = artifact_type.lower()
            if artifact_type_lower not in artifact_urls:
                return f"Invalid artifact type. Supported types: branch, pullrequest, commit, build"
            
            artifact_url = artifact_urls[artifact_type_lower]
            
            document = [
                JsonPatchOperation(
                    op="add",
                    path="/relations/-",
                    value={
                        "rel": "ArtifactLink",
                        "url": artifact_url,
                        "attributes": {
                            "name": artifact_name or artifact_type.capitalize()
                        }
                    }
                )
            ]
            
            work_item = self.wit_client.update_work_item(
                document=document,
                id=work_item_id,
                project=self.project_name
            )
            
            return f"Successfully linked {artifact_type} '{artifact_id}' to work item #{work_item_id}"
        except Exception as e:
            return f"Error adding artifact link: {str(e)}"


def create_azdo_work_items_tools(
    organization_url: str = organization_url,
    personal_access_token: str = personal_access_token,
    project_name: str = project_name
) -> List[Tool]:
    """
    Create LangChain tools for Azure DevOps Work Items operations
    
    Returns:
        List of LangChain Tool objects
    """
    connector = AzureDevOpsWorkItemsConnector(
        organization_url=organization_url,
        personal_access_token=personal_access_token,
        project_name=project_name
    )
    
    tools = [
        Tool(
            name="wit_my_work_items",
            func=lambda x: connector.my_work_items(),
            description="Retrieve work items relevant to the authenticated user. Returns work items assigned to the current user."
        ),
        
        Tool(
            name="wit_get_work_item",
            func=lambda work_item_id: connector.get_work_item(int(work_item_id)),
            description="Get a single work item by ID. Input should be the work item ID (integer)."
        ),
        
        Tool(
            name="wit_get_work_items_batch_by_ids",
            func=lambda ids: connector.get_work_items_batch(
                [int(id.strip()) for id in ids.split(',')]
            ),
            description="Retrieve multiple work items by IDs in batch. Input should be comma-separated work item IDs (e.g., '123,456,789')."
        ),
        
        Tool(
            name="wit_create_work_item",
            func=lambda input_str: connector.create_work_item(
                **eval(input_str)
            ),
            description=(
                "Create a new work item. Input should be a Python dict string with keys: "
                "work_item_type (required, e.g., 'User Story', 'Task', 'Bug'), "
                "title (required), description (optional), assigned_to (optional), "
                "tags (optional), priority (optional, default 2). "
                "Example: \"{'work_item_type': 'Task', 'title': 'New task', 'description': 'Details here'}\""
            )
        ),
        
        Tool(
            name="wit_update_work_item",
            func=lambda input_str: connector.update_work_item(
                **eval(input_str)
            ),
            description=(
                "Update a work item by ID. Input should be a Python dict string with keys: "
                "work_item_id (required, integer), updates (required, dict of field:value pairs). "
                "Example: \"{'work_item_id': 123, 'updates': {'System.State': 'Closed', 'System.Title': 'Updated title'}}\""
            )
        ),
        
        Tool(
            name="wit_add_work_item_comment",
            func=lambda input_str: connector.add_work_item_comment(
                **eval(input_str)
            ),
            description=(
                "Add a comment to a work item. Input should be a Python dict string with keys: "
                "work_item_id (required, integer), comment_text (required, string). "
                "Example: \"{'work_item_id': 123, 'comment_text': 'This is a comment'}\""
            )
        ),
        
        Tool(
            name="wit_list_work_item_comments",
            func=lambda work_item_id: connector.list_work_item_comments(int(work_item_id)),
            description="Retrieve comments for a work item. Input should be the work item ID (integer)."
        ),
        
        Tool(
            name="wit_add_child_work_items",
            func=lambda input_str: connector.add_child_work_items(
                **eval(input_str)
            ),
            description=(
                "Create child work items for a parent work item. Input MUST be a Python dictionary string with keys: "
                "parent_id (required, integer), work_item_type (required, e.g., 'Task'), "
                "titles (required, list of strings). "
                "Format: {\"parent_id\": number, \"work_item_type\": \"type\", \"titles\": [\"title1\", \"title2\"]}. "
                "Example: {\"parent_id\": 123, \"work_item_type\": \"Task\", \"titles\": [\"Task 1\", \"Task 2\"]}"
            )
        ),
        
        Tool(
            name="wit_link_work_items",
            func=lambda input_str: connector.link_work_items(
                **eval(input_str)
            ),
            description=(
                "Link two work items together. Input should be a Python dict string with keys: "
                "source_id (required, integer), target_id (required, integer), "
                "link_type (optional, default 'System.LinkTypes.Related'). "
                "Common link types: 'System.LinkTypes.Related', 'System.LinkTypes.Hierarchy-Forward', "
                "'System.LinkTypes.Hierarchy-Reverse'. "
                "Example: \"{'source_id': 123, 'target_id': 456, 'link_type': 'System.LinkTypes.Related'}\""
            )
        ),
        
        Tool(
            name="wit_get_work_items_for_iteration",
            func=lambda input_str: connector.get_work_items_for_iteration(
                **eval(input_str)
            ),
            description=(
                "Retrieve work items for a specific iteration. Input should be a Python dict string with keys: "
                "team_name (required, string), iteration_path (required, string, e.g., 'ProjectName\\Sprint 1'). "
                "Example: \"{'team_name': 'Team A', 'iteration_path': 'MyProject\\\\Sprint 1'}\""
            )
        ),
        
        Tool(
            name="wit_list_backlogs",
            func=lambda team_name: connector.list_backlogs(team_name),
            description="Retrieve backlogs for a team. Input should be the team name (string)."
        ),
        
        Tool(
            name="wit_list_backlog_work_items",
            func=lambda input_str: connector.get_backlog_work_items(
                **eval(input_str)
            ),
            description=(
                "Retrieve work items for a specific backlog. Input MUST be a Python dictionary string with keys: "
                "team_name (required, string), backlog_id (required, string). "
                "Format: {\"team_name\": \"value\", \"backlog_id\": \"value\"}. "
                "Example: {\"team_name\": \"Team A\", \"backlog_id\": \"Microsoft.RequirementCategory\"}"
            )
        ),
        
        Tool(
            name="wit_query_work_items",
            func=lambda wiql_query: connector.query_work_items(wiql_query),
            description=(
                "Execute a WIQL query to retrieve work items. Input should be a complete WIQL query string. "
                "Example: \"SELECT [System.Id], [System.Title] FROM WorkItems WHERE [System.WorkItemType] = 'Bug' "
                "AND [System.State] = 'Active'\""
            )
        ),
        
        Tool(
            name="wit_link_work_item_to_pull_request",
            func=lambda input_str: connector.link_work_item_to_pull_request(
                **eval(input_str)
            ),
            description=(
                "Link a work item to a pull request. Input should be a Python dict string with keys: "
                "work_item_id (required, integer), pull_request_id (required, integer), "
                "repository_id (required, string - repository GUID or name). "
                "Example: \"{'work_item_id': 123, 'pull_request_id': 456, 'repository_id': 'my-repo'}\""
            )
        ),
        
        Tool(
            name="wit_get_work_item_type",
            func=lambda work_item_type_name: connector.get_work_item_type(work_item_type_name),
            description=(
                "Get a specific work item type definition. Input should be the work item type name "
                "(e.g., 'User Story', 'Task', 'Bug', 'Epic'). Returns fields, states, and metadata."
            )
        ),
        
        Tool(
            name="wit_get_query",
            func=lambda query_id_or_path: connector.get_query(query_id_or_path),
            description=(
                "Get a saved query by its ID or path. Input should be the query ID (GUID) or path "
                "(e.g., 'Shared Queries/My Query'). Returns query details including WIQL."
            )
        ),
        
        Tool(
            name="wit_get_query_results_by_id",
            func=lambda query_id: connector.get_query_results_by_id(query_id),
            description=(
                "Execute a saved query and retrieve results. Input should be the query ID (GUID). "
                "Returns the work items matching the saved query."
            )
        ),
        
        Tool(
            name="wit_update_work_items_batch",
            func=lambda input_str: connector.update_work_items_batch(
                eval(input_str)
            ),
            description=(
                "Update multiple work items in batch. Input should be a Python list of dicts, each with keys: "
                "work_item_id (integer), updates (dict of field:value pairs). "
                "Example: \"[{'work_item_id': 123, 'updates': {'System.State': 'Closed'}}, "
                "{'work_item_id': 456, 'updates': {'System.State': 'Active'}}]\""
            )
        ),
        
        Tool(
            name="wit_work_items_link",
            func=lambda input_str: connector.work_items_link_batch(
                eval(input_str)
            ),
            description=(
                "Link multiple work items together in batch. Input should be a Python list of dicts, each with keys: "
                "source_id (integer), target_id (integer), link_type (optional, default 'System.LinkTypes.Related'). "
                "Example: \"[{'source_id': 123, 'target_id': 456}, {'source_id': 789, 'target_id': 101}]\""
            )
        ),
        
        Tool(
            name="wit_work_item_unlink",
            func=lambda input_str: connector.work_item_unlink(
                **eval(input_str)
            ),
            description=(
                "Unlink one or many links from a work item. Input should be a Python dict string with keys: "
                "work_item_id (required, integer), link_indices (required, list of integers - indices of relations to remove). "
                "Example: \"{'work_item_id': 123, 'link_indices': [0, 2]}\""
            )
        ),
        
        Tool(
            name="wit_add_artifact_link",
            func=lambda input_str: connector.add_artifact_link(
                **eval(input_str)
            ),
            description=(
                "Link to artifacts like branch, pull request, commit, and build. Input should be a Python dict string with keys: "
                "work_item_id (required, integer), artifact_type (required, one of: 'branch', 'pullrequest', 'commit', 'build'), "
                "artifact_id (required, string), artifact_name (optional, string). "
                "Example: \"{'work_item_id': 123, 'artifact_type': 'branch', 'artifact_id': 'repo-id/branch-name', "
                "'artifact_name': 'Feature Branch'}\""
            )
        ),
    ]
    
    return tools


# # Example usage
# if __name__ == "__main__":
#     # Create the tools
#     tools = create_azdo_work_items_tools()
    
#     print(f"Created {len(tools)} Azure DevOps Work Items tools:")
#     for tool in tools:
#         print(f"  - {tool.name}: {tool.description[:80]}...")
    
#     # Example: Get my work items
#     print("\n=== Example: Getting my work items ===")
#     my_work_items_tool = next(t for t in tools if t.name == "wit_my_work_items")
#     result = my_work_items_tool.run("")
#     print(result)