import os
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv
from langchain.tools import Tool
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from azure.devops.v7_0.build.models import (
    Build,
    BuildDefinitionReference,
    DefinitionReference,
    UpdateStageParameters
)
from azure.devops.v7_0.pipelines.models import (
    RunPipelineParameters as PipelineRunParameters,
    RunResourcesParameters,
    RunResources
)
import json

load_dotenv()

# Configuration
organization_url = os.getenv('AZURE_ORG_URL', 'https://dev.azure.com/yourorg')
personal_access_token = os.getenv('AZURE_DEVOPS_PERSONAL_ACCESS_TOKEN', 'your-pat-token')
project_name = os.getenv('PROJECT_NAME', 'YourProject')


class AzureDevOpsPipelinesConnector:
    """Azure DevOps Pipelines Connector using PAT authentication"""
    
    def __init__(self, organization_url: str, personal_access_token: str, project_name: str):
        self.organization_url = organization_url
        self.project_name = project_name
        credentials = BasicAuthentication('', personal_access_token)
        self.connection = Connection(base_url=organization_url, creds=credentials)
        self.build_client = self.connection.clients.get_build_client()
        self.pipelines_client = self.connection.clients.get_pipelines_client()
    
    def get_build_definitions(self, name_filter: str = None, top: int = 50) -> str:
        """Retrieve a list of build definitions for a given project"""
        try:
            definitions = self.build_client.get_definitions(
                project=self.project_name,
                name=name_filter,
                top=top
            )
            
            if not definitions:
                return f"No build definitions found in project '{self.project_name}'"
            
            result = f"Found {len(definitions)} build definitions:\n\n"
            for definition in definitions:
                result += f"ID: {definition.id}\n"
                result += f"Name: {definition.name}\n"
                result += f"Path: {definition.path}\n"
                result += f"Type: {definition.type}\n"
                result += f"Queue Status: {definition.queue_status}\n"
                result += f"Revision: {definition.revision}\n"
                if definition.repository:
                    result += f"Repository: {definition.repository.name}\n"
                result += f"URL: {definition.url}\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error retrieving build definitions: {str(e)}"
    
    def get_build_definition_revisions(self, definition_id: int) -> str:
        """Retrieve a list of revisions for a specific build definition"""
        try:
            revisions = self.build_client.get_definition_revisions(
                project=self.project_name,
                definition_id=definition_id
            )
            
            if not revisions:
                return f"No revisions found for build definition {definition_id}"
            
            result = f"Found {len(revisions)} revisions for build definition {definition_id}:\n\n"
            for revision in revisions:
                result += f"Revision: {revision.revision}\n"
                result += f"Name: {revision.name}\n"
                result += f"Changed By: {revision.changed_by.display_name if revision.changed_by else 'Unknown'}\n"
                result += f"Changed Date: {revision.changed_date}\n"
                result += f"Comment: {revision.comment if hasattr(revision, 'comment') else 'N/A'}\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error retrieving definition revisions: {str(e)}"
    
    def get_builds(self, definition_ids: List[int] = None, 
                   status_filter: str = None, 
                   result_filter: str = None,
                   top: int = 50) -> str:
        """Retrieve a list of builds for a given project"""
        try:
            # Map string filters to enum values if provided
            build_status = None
            build_result = None
            
            if status_filter:
                status_map = {
                    'inprogress': 1,
                    'completed': 2,
                    'cancelling': 4,
                    'postponed': 8,
                    'notstarted': 32,
                    'all': 47
                }
                build_status = status_map.get(status_filter.lower())
            
            if result_filter:
                result_map = {
                    'succeeded': 2,
                    'partiallysucceeded': 4,
                    'failed': 8,
                    'canceled': 32
                }
                build_result = result_map.get(result_filter.lower())
            
            builds = self.build_client.get_builds(
                project=self.project_name,
                definitions=definition_ids,
                status_filter=build_status,
                result_filter=build_result,
                top=top
            )
            
            if not builds:
                return "No builds found matching the criteria"
            
            result = f"Found {len(builds)} builds:\n\n"
            for build in builds:
                result += f"Build ID: {build.id}\n"
                result += f"Build Number: {build.build_number}\n"
                result += f"Definition: {build.definition.name}\n"
                result += f"Status: {build.status}\n"
                result += f"Result: {build.result}\n"
                result += f"Source Branch: {build.source_branch}\n"
                result += f"Source Version: {build.source_version[:12] if build.source_version else 'N/A'}\n"
                result += f"Requested By: {build.requested_by.display_name if build.requested_by else 'Unknown'}\n"
                result += f"Queue Time: {build.queue_time}\n"
                result += f"Start Time: {build.start_time}\n"
                result += f"Finish Time: {build.finish_time}\n"
                result += f"URL: {build.url}\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error retrieving builds: {str(e)}"
    
    def get_build_log(self, build_id: int) -> str:
        """Retrieve the logs for a specific build"""
        try:
            # Get all logs for the build
            logs = self.build_client.get_build_logs(
                project=self.project_name,
                build_id=build_id
            )
            
            if not logs:
                return f"No logs found for build {build_id}"
            
            result = f"Build {build_id} has {len(logs)} log files:\n\n"
            
            # List all log files
            for log in logs:
                result += f"Log ID: {log.id}\n"
                result += f"Type: {log.type}\n"
                result += f"URL: {log.url}\n"
                result += f"Line Count: {log.line_count if hasattr(log, 'line_count') else 'N/A'}\n"
                
                # Fetch the actual log content for each log
                try:
                    log_content = self.build_client.get_build_log_lines(
                        project=self.project_name,
                        build_id=build_id,
                        log_id=log.id
                    )
                    if log_content:
                        result += f"Content Preview (first 20 lines):\n"
                        for i, line in enumerate(log_content[:20]):
                            result += f"  {line}\n"
                        if len(log_content) > 20:
                            result += f"  ... ({len(log_content) - 20} more lines)\n"
                except:
                    result += "Content: Unable to fetch log content\n"
                
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error retrieving build logs: {str(e)}"
    
    def get_build_log_by_id(self, build_id: int, log_id: int) -> str:
        """Get a specific build log by log ID"""
        try:
            log_lines = self.build_client.get_build_log_lines(
                project=self.project_name,
                build_id=build_id,
                log_id=log_id
            )
            
            if not log_lines:
                return f"No log content found for build {build_id}, log {log_id}"
            
            result = f"Build {build_id} - Log {log_id} ({len(log_lines)} lines):\n\n"
            for line in log_lines:
                result += f"{line}\n"
            
            return result
        except Exception as e:
            return f"Error retrieving build log: {str(e)}"
    
    def get_build_changes(self, build_id: int, top: int = 50) -> str:
        """Get the changes associated with a specific build"""
        try:
            changes = self.build_client.get_build_changes(
                project=self.project_name,
                build_id=build_id,
                top=top
            )
            
            if not changes:
                return f"No changes found for build {build_id}"
            
            result = f"Found {len(changes)} changes for build {build_id}:\n\n"
            for change in changes:
                result += f"Change ID: {change.id}\n"
                result += f"Type: {change.type}\n"
                result += f"Author: {change.author.display_name if change.author else 'Unknown'}\n"
                result += f"Timestamp: {change.timestamp}\n"
                result += f"Message: {change.message}\n"
                result += f"Location: {change.location}\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error retrieving build changes: {str(e)}"
    
    def get_build_status(self, build_id: int) -> str:
        """Fetch the status of a specific build"""
        try:
            build = self.build_client.get_build(
                project=self.project_name,
                build_id=build_id
            )
            
            result = f"Build Status for Build #{build_id}:\n\n"
            result += f"Build Number: {build.build_number}\n"
            result += f"Definition: {build.definition.name}\n"
            result += f"Status: {build.status}\n"
            result += f"Result: {build.result}\n"
            result += f"Source Branch: {build.source_branch}\n"
            result += f"Source Version: {build.source_version}\n"
            result += f"Queue Time: {build.queue_time}\n"
            result += f"Start Time: {build.start_time}\n"
            result += f"Finish Time: {build.finish_time}\n"
            result += f"Requested By: {build.requested_by.display_name if build.requested_by else 'Unknown'}\n"
            result += f"Requested For: {build.requested_for.display_name if build.requested_for else 'Unknown'}\n"
            
            # Get timeline for stage information
            try:
                timeline = self.build_client.get_build_timeline(
                    project=self.project_name,
                    build_id=build_id
                )
                
                if timeline and timeline.records:
                    result += f"\nStages/Jobs ({len(timeline.records)}):\n"
                    for record in timeline.records:
                        if record.type in ['Stage', 'Job', 'Phase']:
                            result += f"  - {record.name} ({record.type}): {record.state} - {record.result}\n"
            except:
                pass
            
            result += f"\nURL: {build.url}\n"
            
            return result
        except Exception as e:
            return f"Error retrieving build status: {str(e)}"
    
    def update_build_stage(self, build_id: int, stage_ref_name: str, 
                          state: str, force_retry: bool = False) -> str:
        """Update the stage of a specific build"""
        try:
            # Get the build timeline to find the stage
            timeline = self.build_client.get_build_timeline(
                project=self.project_name,
                build_id=build_id
            )
            
            stage_id = None
            if timeline and timeline.records:
                for record in timeline.records:
                    if record.type == 'Stage' and (record.name == stage_ref_name or 
                                                   record.identifier == stage_ref_name):
                        stage_id = record.id
                        break
            
            if not stage_id:
                return f"Stage '{stage_ref_name}' not found in build {build_id}"
            
            # Update the stage
            update_params = UpdateStageParameters()
            update_params.state = state
            update_params.force_retry_all_jobs = force_retry
            
            result = self.build_client.update_build_stage(
                update_parameters=update_params,
                build_id=build_id,
                stage_ref_name=stage_id,
                project=self.project_name
            )
            
            return f"Successfully updated stage '{stage_ref_name}' in build {build_id}\n" \
                   f"New State: {state}"
        except Exception as e:
            return f"Error updating build stage: {str(e)}"
    
    def get_run(self, pipeline_id: int, run_id: int) -> str:
        """Get a run for a particular pipeline"""
        try:
            run = self.pipelines_client.get_run(
                project=self.project_name,
                pipeline_id=pipeline_id,
                run_id=run_id
            )
            
            result = f"Pipeline Run Details:\n\n"
            result += f"Run ID: {run.id}\n"
            result += f"Name: {run.name}\n"
            result += f"Pipeline ID: {run.pipeline.id}\n"
            result += f"Pipeline Name: {run.pipeline.name}\n"
            result += f"State: {run.state}\n"
            result += f"Result: {run.result}\n"
            result += f"Created Date: {run.created_date}\n"
            result += f"Finished Date: {run.finished_date}\n"
            result += f"URL: {run.url}\n"
            
            if run.resources:
                result += f"\nResources:\n"
                if run.resources.repositories:
                    for repo_name, repo in run.resources.repositories.items():
                        result += f"  Repository: {repo_name}\n"
                        result += f"    Ref: {repo.ref_name if hasattr(repo, 'ref_name') else 'N/A'}\n"
                        result += f"    Version: {repo.version if hasattr(repo, 'version') else 'N/A'}\n"
            
            return result
        except Exception as e:
            return f"Error retrieving pipeline run: {str(e)}"
    
    def list_runs(self, pipeline_id: int, top: int = 100) -> str:
        """Get runs for a particular pipeline (up to 10000)"""
        try:
            runs = self.pipelines_client.list_runs(
                project=self.project_name,
                pipeline_id=pipeline_id,
                top=min(top, 10000)  # API limit
            )
            
            if not runs:
                return f"No runs found for pipeline {pipeline_id}"
            
            result = f"Found {len(runs)} runs for pipeline {pipeline_id}:\n\n"
            for run in runs:
                result += f"Run ID: {run.id}\n"
                result += f"Name: {run.name}\n"
                result += f"State: {run.state}\n"
                result += f"Result: {run.result}\n"
                result += f"Created Date: {run.created_date}\n"
                result += f"Finished Date: {run.finished_date}\n"
                result += f"URL: {run.url}\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error listing pipeline runs: {str(e)}"
    
    def run_pipeline(self, pipeline_id: int, branch: str = None, 
                    variables: Dict[str, str] = None,
                    stages_to_skip: List[str] = None) -> str:
        """Start a new run of a pipeline"""
        try:
            # Create run parameters
            run_params = PipelineRunParameters()
            
            # Set branch/resources
            if branch:
                resources = RunResources()
                resources.repositories = {
                    "self": {
                        "refName": f"refs/heads/{branch}" if not branch.startswith("refs/") else branch
                    }
                }
                run_params.resources = resources
            
            # Set variables
            if variables:
                run_params.variables = variables
            
            # Set stages to skip
            if stages_to_skip:
                run_params.stages_to_skip = stages_to_skip
            
            # Start the pipeline run
            run = self.pipelines_client.run_pipeline(
                run_parameters=run_params,
                project=self.project_name,
                pipeline_id=pipeline_id
            )
            
            result = f"Successfully started pipeline run:\n\n"
            result += f"Run ID: {run.id}\n"
            result += f"Name: {run.name}\n"
            result += f"Pipeline ID: {run.pipeline.id}\n"
            result += f"Pipeline Name: {run.pipeline.name}\n"
            result += f"State: {run.state}\n"
            result += f"Created Date: {run.created_date}\n"
            result += f"URL: {run.url}\n"
            
            return result
        except Exception as e:
            return f"Error running pipeline: {str(e)}"


def create_azdo_pipelines_tools(
    organization_url: str = organization_url,
    personal_access_token: str = personal_access_token,
    project_name: str = project_name
) -> List[Tool]:
    """
    Create LangChain tools for Azure DevOps Pipelines operations
    
    Returns:
        List of LangChain Tool objects
    """
    connector = AzureDevOpsPipelinesConnector(
        organization_url=organization_url,
        personal_access_token=personal_access_token,
        project_name=project_name
    )
    
    tools = [
        Tool(
            name="pipelines_get_build_definitions",
            func=lambda input_str: connector.get_build_definitions(
                **eval(input_str) if input_str.strip() else {}
            ),
            description=(
                "Retrieve build definitions for the project. Input should be a Python dict string with keys: "
                "name_filter (optional, string - filter by name), top (optional, integer, default 50). "
                "Example: \"{'name_filter': 'MyPipeline', 'top': 10}\" or \"{}\" for all definitions"
            )
        ),
        
        Tool(
            name="pipelines_get_build_definition_revisions",
            func=lambda definition_id: connector.get_build_definition_revisions(int(definition_id)),
            description=(
                "Retrieve revisions for a build definition. Input should be the definition ID (integer). "
                "Shows history of changes to the pipeline definition."
            )
        ),
        
        Tool(
            name="pipelines_get_builds",
            func=lambda input_str: connector.get_builds(
                **eval(input_str) if input_str.strip() else {}
            ),
            description=(
                "Retrieve builds for the project. Input should be a Python dict string with keys: "
                "definition_ids (optional, list of integers), status_filter (optional, one of: 'inprogress', 'completed', 'cancelling', 'postponed', 'notstarted', 'all'), "
                "result_filter (optional, one of: 'succeeded', 'partiallysucceeded', 'failed', 'canceled'), top (optional, integer, default 50). "
                "Example: \"{'definition_ids': [123], 'status_filter': 'completed', 'top': 20}\" or \"{}\" for recent builds"
            )
        ),
        
        Tool(
            name="pipelines_get_build_log",
            func=lambda build_id: connector.get_build_log(int(build_id)),
            description=(
                "Retrieve all logs for a specific build. Input should be the build ID (integer). "
                "Returns all log files with preview of content."
            )
        ),
        
        Tool(
            name="pipelines_get_build_log_by_id",
            func=lambda input_str: connector.get_build_log_by_id(
                **eval(input_str)
            ),
            description=(
                "Get a specific build log by log ID. Input should be a Python dict string with keys: "
                "build_id (required, integer), log_id (required, integer). "
                "Example: \"{'build_id': 123, 'log_id': 456}\""
            )
        ),
        
        Tool(
            name="pipelines_get_build_changes",
            func=lambda input_str: connector.get_build_changes(
                **eval(input_str) if isinstance(eval(input_str), dict) else {'build_id': int(input_str)}
            ),
            description=(
                "Get changes (commits) associated with a build. Input should be a Python dict string with keys: "
                "build_id (required, integer), top (optional, integer, default 50). "
                "Example: \"{'build_id': 123, 'top': 10}\" or just \"123\" for build ID"
            )
        ),
        
        Tool(
            name="pipelines_get_build_status",
            func=lambda build_id: connector.get_build_status(int(build_id)),
            description=(
                "Fetch detailed status of a specific build. Input should be the build ID (integer). "
                "Returns status, result, timing, stages, and jobs information."
            )
        ),
        
        Tool(
            name="pipelines_update_build_stage",
            func=lambda input_str: connector.update_build_stage(
                **eval(input_str)
            ),
            description=(
                "Update the stage of a specific build. Input should be a Python dict string with keys: "
                "build_id (required, integer), stage_ref_name (required, string - stage name or ID), "
                "state (required, string - new state), force_retry (optional, boolean, default False). "
                "Example: \"{'build_id': 123, 'stage_ref_name': 'Build', 'state': 'retry', 'force_retry': True}\""
            )
        ),
        
        Tool(
            name="pipelines_get_run",
            func=lambda input_str: connector.get_run(
                **eval(input_str)
            ),
            description=(
                "Get a run for a particular pipeline. Input should be a Python dict string with keys: "
                "pipeline_id (required, integer), run_id (required, integer). "
                "Example: \"{'pipeline_id': 123, 'run_id': 456}\""
            )
        ),
        
        Tool(
            name="pipelines_list_runs",
            func=lambda input_str: connector.list_runs(
                **eval(input_str)
            ),
            description=(
                "Get runs for a pipeline (up to 10000). Input should be a Python dict string with keys: "
                "pipeline_id (required, integer), top (optional, integer, default 100, max 10000). "
                "Example: \"{'pipeline_id': 123, 'top': 50}\""
            )
        ),
        
        Tool(
            name="pipelines_run_pipeline",
            func=lambda input_str: connector.run_pipeline(
                **eval(input_str)
            ),
            description=(
                "Start a new run of a pipeline. Input should be a Python dict string with keys: "
                "pipeline_id (required, integer), branch (optional, string - branch to run from), "
                "variables (optional, dict of variable name:value pairs), stages_to_skip (optional, list of stage names to skip). "
                "Example: \"{'pipeline_id': 123, 'branch': 'main', 'variables': {'BuildConfiguration': 'Release'}}\""
            )
        ),
    ]
    
    return tools


# # Example usage
# if __name__ == "__main__":
#     # Create the tools
#     tools = create_azdo_pipelines_tools()
    
#     print(f"Created {len(tools)} Azure DevOps Pipelines tools:")
#     for tool in tools:
#         print(f"  - {tool.name}: {tool.description[:80]}...")
    
#     # Example: Get build definitions
#     print("\n=== Example: Getting build definitions ===")
#     get_definitions_tool = next(t for t in tools if t.name == "pipelines_get_build_definitions")
#     result = get_definitions_tool.run("{}")
#     print(result)