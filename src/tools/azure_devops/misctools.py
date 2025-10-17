import os
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv
from langchain.tools import Tool
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from azure.devops.v7_0.test.models import (
    TestPlan,
    TestSuite,
    SuiteTestCase,
    WorkItemReference
)
from azure.devops.v7_0.wiki.models import (
    WikiPageCreateOrUpdateParameters,
    WikiCreateParametersV2
)
from azure.devops.v7_0.work.models import (
    TeamContext,
    TeamSettingsIteration
)
from azure.devops.v7_0.work_item_tracking.models import JsonPatchOperation
from azure.devops.v7_0.search.models import (
    CodeSearchRequest,
    WikiSearchRequest,
    WorkItemSearchRequest
)
import json

load_dotenv()

# Configuration
organization_url = os.getenv('AZURE_ORG_URL', 'https://dev.azure.com/yourorg')
personal_access_token = os.getenv('AZURE_DEVOPS_PERSONAL_ACCESS_TOKEN', 'your-pat-token')
project_name = os.getenv('PROJECT_NAME', 'YourProject')


class AzureDevOpsAdditionalServicesConnector:
    """Azure DevOps Additional Services Connector (Security, Test, Wiki, Search, Core, Work)"""
    
    def __init__(self, organization_url: str, personal_access_token: str, project_name: str):
        self.organization_url = organization_url
        self.project_name = project_name
        credentials = BasicAuthentication('', personal_access_token)
        self.connection = Connection(base_url=organization_url, creds=credentials)
        
        # Initialize clients
        self.test_client = self.connection.clients.get_test_client()
        self.wiki_client = self.connection.clients.get_wiki_client()
        self.work_client = self.connection.clients.get_work_client()
        self.core_client = self.connection.clients.get_core_client()
        self.wit_client = self.connection.clients.get_work_item_tracking_client()
        self.build_client = self.connection.clients.get_build_client()
        
        # Search client (may need separate handling)
        try:
            self.search_client = self.connection.clients_v7_1.get_search_client()
        except:
            self.search_client = None
    
    # ========== Advanced Security ==========
    
    def get_alerts(self, repository_id: str, criteria: Dict[str, Any] = None) -> str:
        """Retrieve Advanced Security alerts for a repository"""
        try:
            # Note: Advanced Security may require specific API or extension
            # This is a placeholder implementation
            result = f"Advanced Security Alerts for repository '{repository_id}':\n\n"
            result += "Note: Advanced Security requires GitHub Advanced Security for Azure DevOps.\n"
            result += "This feature may require additional API endpoints not available in standard SDK.\n"
            
            return result
        except Exception as e:
            return f"Error retrieving security alerts: {str(e)}"
    
    def get_alert_details(self, repository_id: str, alert_id: int) -> str:
        """Get detailed information about a specific Advanced Security alert"""
        try:
            result = f"Advanced Security Alert Details:\n\n"
            result += f"Alert ID: {alert_id}\n"
            result += f"Repository: {repository_id}\n"
            result += "Note: Advanced Security requires GitHub Advanced Security for Azure DevOps.\n"
            
            return result
        except Exception as e:
            return f"Error retrieving alert details: {str(e)}"
    
    # ========== Test Plans ==========
    
    def create_test_plan(self, name: str, area_path: str = None, 
                        iteration_path: str = None, description: str = "") -> str:
        """Create a new test plan"""
        try:
            test_plan = TestPlan()
            test_plan.name = name
            test_plan.description = description
            
            if area_path:
                test_plan.area_path = area_path
            if iteration_path:
                test_plan.iteration = iteration_path
            
            created_plan = self.test_client.create_test_plan(
                test_plan=test_plan,
                project=self.project_name
            )
            
            return f"Successfully created test plan:\n" \
                   f"ID: {created_plan.id}\n" \
                   f"Name: {created_plan.name}\n" \
                   f"URL: {created_plan.url}"
        except Exception as e:
            return f"Error creating test plan: {str(e)}"
    
    def create_test_case(self, title: str, steps: List[Dict[str, str]] = None,
                        area_path: str = None, priority: int = 2) -> str:
        """Create a new test case work item"""
        try:
            document = []
            
            # Add title
            document.append(JsonPatchOperation(
                op="add",
                path="/fields/System.Title",
                value=title
            ))
            
            # Add work item type
            document.append(JsonPatchOperation(
                op="add",
                path="/fields/System.WorkItemType",
                value="Test Case"
            ))
            
            # Add area path
            if area_path:
                document.append(JsonPatchOperation(
                    op="add",
                    path="/fields/System.AreaPath",
                    value=area_path
                ))
            
            # Add priority
            document.append(JsonPatchOperation(
                op="add",
                path="/fields/Microsoft.VSTS.Common.Priority",
                value=priority
            ))
            
            # Add test steps if provided
            if steps:
                steps_xml = "<steps id='0' last='{}'>".format(len(steps))
                for i, step in enumerate(steps, 1):
                    action = step.get('action', '')
                    expected = step.get('expected', '')
                    steps_xml += f"<step id='{i}' type='ActionStep'>"
                    steps_xml += f"<parameterizedString isformatted='true'>&lt;DIV&gt;&lt;P&gt;{action}&lt;/P&gt;&lt;/DIV&gt;</parameterizedString>"
                    steps_xml += f"<parameterizedString isformatted='true'>&lt;DIV&gt;&lt;P&gt;{expected}&lt;/P&gt;&lt;/DIV&gt;</parameterizedString>"
                    steps_xml += f"<description/></step>"
                steps_xml += "</steps>"
                
                document.append(JsonPatchOperation(
                    op="add",
                    path="/fields/Microsoft.VSTS.TCM.Steps",
                    value=steps_xml
                ))
            
            test_case = self.wit_client.create_work_item(
                document=document,
                project=self.project_name,
                type="Test Case"
            )
            
            return f"Successfully created test case:\n" \
                   f"ID: {test_case.id}\n" \
                   f"Title: {title}\n" \
                   f"URL: {test_case.url}"
        except Exception as e:
            return f"Error creating test case: {str(e)}"
    
    def update_test_case_steps(self, test_case_id: int, steps: List[Dict[str, str]]) -> str:
        """Update an existing test case work item's steps"""
        try:
            steps_xml = "<steps id='0' last='{}'>".format(len(steps))
            for i, step in enumerate(steps, 1):
                action = step.get('action', '')
                expected = step.get('expected', '')
                steps_xml += f"<step id='{i}' type='ActionStep'>"
                steps_xml += f"<parameterizedString isformatted='true'>&lt;DIV&gt;&lt;P&gt;{action}&lt;/P&gt;&lt;/DIV&gt;</parameterizedString>"
                steps_xml += f"<parameterizedString isformatted='true'>&lt;DIV&gt;&lt;P&gt;{expected}&lt;/P&gt;&lt;/DIV&gt;</parameterizedString>"
                steps_xml += f"<description/></step>"
            steps_xml += "</steps>"
            
            document = [
                JsonPatchOperation(
                    op="add",
                    path="/fields/Microsoft.VSTS.TCM.Steps",
                    value=steps_xml
                )
            ]
            
            self.wit_client.update_work_item(
                document=document,
                id=test_case_id,
                project=self.project_name
            )
            
            return f"Successfully updated test case {test_case_id} with {len(steps)} steps"
        except Exception as e:
            return f"Error updating test case steps: {str(e)}"
    
    def add_test_cases_to_suite(self, plan_id: int, suite_id: int, 
                               test_case_ids: List[int]) -> str:
        """Add existing test cases to a test suite"""
        try:
            for test_case_id in test_case_ids:
                self.test_client.add_test_cases_to_suite(
                    project=self.project_name,
                    plan_id=plan_id,
                    suite_id=suite_id,
                    test_case_id=test_case_id
                )
            
            return f"Successfully added {len(test_case_ids)} test cases to suite {suite_id}"
        except Exception as e:
            return f"Error adding test cases to suite: {str(e)}"
    
    def list_test_plans(self, active_only: bool = True, detailed: bool = False) -> str:
        """Retrieve a list of test plans"""
        try:
            test_plans = self.test_client.get_plans(
                project=self.project_name
            )
            
            if not test_plans:
                return "No test plans found"
            
            # Filter active if requested
            if active_only:
                test_plans = [p for p in test_plans if p.state == 'Active']
            
            result = f"Found {len(test_plans)} test plans:\n\n"
            for plan in test_plans:
                result += f"ID: {plan.id}\n"
                result += f"Name: {plan.name}\n"
                result += f"State: {plan.state}\n"
                
                if detailed:
                    result += f"Area Path: {plan.area_path}\n"
                    result += f"Iteration: {plan.iteration}\n"
                    result += f"Description: {plan.description}\n"
                    result += f"Owner: {plan.owner.display_name if plan.owner else 'Unknown'}\n"
                
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error retrieving test plans: {str(e)}"
    
    def list_test_cases(self, plan_id: int, suite_id: int = None) -> str:
        """Get a list of test cases in a test plan"""
        try:
            if suite_id:
                test_cases = self.test_client.get_test_cases(
                    project=self.project_name,
                    plan_id=plan_id,
                    suite_id=suite_id
                )
            else:
                # Get all suites first, then all test cases
                suites = self.test_client.get_test_suites_for_plan(
                    project=self.project_name,
                    plan_id=plan_id
                )
                test_cases = []
                for suite in suites:
                    cases = self.test_client.get_test_cases(
                        project=self.project_name,
                        plan_id=plan_id,
                        suite_id=suite.id
                    )
                    test_cases.extend(cases)
            
            if not test_cases:
                return f"No test cases found in plan {plan_id}"
            
            result = f"Found {len(test_cases)} test cases:\n\n"
            for test_case in test_cases:
                result += f"ID: {test_case.test_case.id}\n"
                result += f"Name: {test_case.test_case.name}\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error retrieving test cases: {str(e)}"
    
    def show_test_results_from_build_id(self, build_id: int) -> str:
        """Get test results for a given build ID"""
        try:
            test_results = self.test_client.get_test_results_by_build(
                project=self.project_name,
                build_id=build_id
            )
            
            if not test_results:
                return f"No test results found for build {build_id}"
            
            result = f"Found {len(test_results)} test results for build {build_id}:\n\n"
            
            passed = sum(1 for r in test_results if r.outcome == 'Passed')
            failed = sum(1 for r in test_results if r.outcome == 'Failed')
            
            result += f"Summary: {passed} Passed, {failed} Failed\n\n"
            
            for test_result in test_results:
                result += f"Test: {test_result.test_case_title}\n"
                result += f"Outcome: {test_result.outcome}\n"
                result += f"Duration: {test_result.duration_in_ms}ms\n"
                if test_result.error_message:
                    result += f"Error: {test_result.error_message}\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error retrieving test results: {str(e)}"
    
    def create_test_suite(self, plan_id: int, suite_name: str, 
                         parent_suite_id: int = None, suite_type: str = "StaticTestSuite") -> str:
        """Create a new test suite in a test plan"""
        try:
            test_suite = TestSuite()
            test_suite.name = suite_name
            test_suite.suite_type = suite_type
            
            if parent_suite_id:
                test_suite.parent_suite = TestSuite(id=parent_suite_id)
            
            created_suite = self.test_client.create_test_suite(
                test_suite=test_suite,
                project=self.project_name,
                plan_id=plan_id
            )
            
            return f"Successfully created test suite:\n" \
                   f"ID: {created_suite.id}\n" \
                   f"Name: {created_suite.name}\n" \
                   f"Type: {created_suite.suite_type}"
        except Exception as e:
            return f"Error creating test suite: {str(e)}"
    
    # ========== Wiki ==========
    
    def list_wikis(self) -> str:
        """Retrieve a list of wikis"""
        try:
            wikis = self.wiki_client.get_all_wikis(project=self.project_name)
            
            if not wikis:
                return "No wikis found"
            
            result = f"Found {len(wikis)} wikis:\n\n"
            for wiki in wikis:
                result += f"ID: {wiki.id}\n"
                result += f"Name: {wiki.name}\n"
                result += f"Type: {wiki.type}\n"
                result += f"URL: {wiki.url}\n"
                if wiki.repository:
                    result += f"Repository: {wiki.repository.name}\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error retrieving wikis: {str(e)}"
    
    def get_wiki(self, wiki_identifier: str) -> str:
        """Get the wiki by identifier"""
        try:
            wiki = self.wiki_client.get_wiki(
                project=self.project_name,
                wiki_identifier=wiki_identifier
            )
            
            result = f"Wiki Details:\n\n"
            result += f"ID: {wiki.id}\n"
            result += f"Name: {wiki.name}\n"
            result += f"Type: {wiki.type}\n"
            result += f"URL: {wiki.url}\n"
            
            if wiki.repository:
                result += f"Repository: {wiki.repository.name}\n"
                result += f"Mapped Path: {wiki.mapped_path}\n"
            
            return result
        except Exception as e:
            return f"Error retrieving wiki: {str(e)}"
    
    def list_pages(self, wiki_identifier: str, path: str = "/") -> str:
        """Retrieve a list of wiki pages"""
        try:
            pages = self.wiki_client.get_pages_batch(
                project=self.project_name,
                wiki_identifier=wiki_identifier,
                path=path
            )
            
            if not pages:
                return f"No pages found in wiki '{wiki_identifier}'"
            
            result = f"Found {len(pages)} pages:\n\n"
            for page in pages:
                result += f"Path: {page.path}\n"
                if hasattr(page, 'git_item_path'):
                    result += f"Git Path: {page.git_item_path}\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error retrieving wiki pages: {str(e)}"
    
    def get_page(self, wiki_identifier: str, page_path: str) -> str:
        """Retrieve wiki page metadata"""
        try:
            page = self.wiki_client.get_page(
                project=self.project_name,
                wiki_identifier=wiki_identifier,
                path=page_path
            )
            
            result = f"Wiki Page Details:\n\n"
            result += f"Path: {page.path}\n"
            result += f"Git Item Path: {page.git_item_path if hasattr(page, 'git_item_path') else 'N/A'}\n"
            result += f"URL: {page.remote_url if hasattr(page, 'remote_url') else 'N/A'}\n"
            
            return result
        except Exception as e:
            return f"Error retrieving wiki page: {str(e)}"
    
    def get_page_content(self, wiki_identifier: str, page_path: str) -> str:
        """Retrieve wiki page content"""
        try:
            page = self.wiki_client.get_page_text(
                project=self.project_name,
                wiki_identifier=wiki_identifier,
                path=page_path
            )
            
            result = f"Wiki Page Content (Path: {page_path}):\n\n"
            result += page
            
            return result
        except Exception as e:
            return f"Error retrieving wiki page content: {str(e)}"
    
    def create_or_update_page(self, wiki_identifier: str, page_path: str, 
                             content: str, comment: str = "") -> str:
        """Create or update wiki pages"""
        try:
            # Check if page exists
            try:
                existing_page = self.wiki_client.get_page(
                    project=self.project_name,
                    wiki_identifier=wiki_identifier,
                    path=page_path
                )
                version = existing_page.e_tag if hasattr(existing_page, 'e_tag') else None
                action = "Updated"
            except:
                version = None
                action = "Created"
            
            parameters = WikiPageCreateOrUpdateParameters()
            parameters.content = content
            
            page = self.wiki_client.create_or_update_page(
                parameters=parameters,
                project=self.project_name,
                wiki_identifier=wiki_identifier,
                path=page_path,
                version=version,
                comment=comment
            )
            
            return f"{action} wiki page successfully:\n" \
                   f"Path: {page.path}\n" \
                   f"URL: {page.remote_url if hasattr(page, 'remote_url') else 'N/A'}"
        except Exception as e:
            return f"Error creating/updating wiki page: {str(e)}"
    
    # ========== Search ==========
    
    def search_code(self, search_text: str, top: int = 50) -> str:
        """Get code search results"""
        try:
            if not self.search_client:
                return "Search client not available. Code search may require additional configuration."
            
            search_request = CodeSearchRequest()
            search_request.search_text = search_text
            search_request.top = top
            
            results = self.search_client.fetch_code_search_results(
                request=search_request,
                project=self.project_name
            )
            
            if not results or not results.results:
                return f"No code search results found for '{search_text}'"
            
            result = f"Found {results.count} code search results:\n\n"
            for item in results.results:
                result += f"File: {item.path}\n"
                result += f"Repository: {item.repository}\n"
                result += f"Project: {item.project}\n"
                result += f"Matches: {item.matches}\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error searching code: {str(e)}"
    
    def search_wiki(self, search_text: str, top: int = 50) -> str:
        """Get wiki search results"""
        try:
            if not self.search_client:
                return "Search client not available. Wiki search may require additional configuration."
            
            search_request = WikiSearchRequest()
            search_request.search_text = search_text
            search_request.top = top
            
            results = self.search_client.fetch_wiki_search_results(
                request=search_request,
                project=self.project_name
            )
            
            if not results or not results.results:
                return f"No wiki search results found for '{search_text}'"
            
            result = f"Found {results.count} wiki search results:\n\n"
            for item in results.results:
                result += f"Title: {item.title}\n"
                result += f"Path: {item.path}\n"
                result += f"Wiki: {item.wiki_name}\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error searching wiki: {str(e)}"
    
    def search_workitem(self, search_text: str, top: int = 50) -> str:
        """Get work item search results"""
        try:
            if not self.search_client:
                return "Search client not available. Work item search may require additional configuration."
            
            search_request = WorkItemSearchRequest()
            search_request.search_text = search_text
            search_request.top = top
            
            results = self.search_client.fetch_work_item_search_results(
                request=search_request,
                project=self.project_name
            )
            
            if not results or not results.results:
                return f"No work item search results found for '{search_text}'"
            
            result = f"Found {results.count} work item search results:\n\n"
            for item in results.results:
                result += f"ID: {item.id}\n"
                result += f"Title: {item.title}\n"
                result += f"Type: {item.work_item_type}\n"
                result += f"State: {item.state}\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error searching work items: {str(e)}"
    
    # ========== Core ==========
    
    def list_project_teams(self) -> str:
        """Retrieve a list of teams for the project"""
        try:
            teams = self.core_client.get_teams(project_id=self.project_name)
            
            if not teams:
                return f"No teams found in project '{self.project_name}'"
            
            result = f"Found {len(teams)} teams:\n\n"
            for team in teams:
                result += f"ID: {team.id}\n"
                result += f"Name: {team.name}\n"
                result += f"Description: {team.description}\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error retrieving teams: {str(e)}"
    
    def list_projects(self) -> str:
        """Retrieve a list of projects in the organization"""
        try:
            projects = self.core_client.get_projects()
            
            if not projects:
                return "No projects found"
            
            result = f"Found {len(projects)} projects:\n\n"
            for project in projects:
                result += f"ID: {project.id}\n"
                result += f"Name: {project.name}\n"
                result += f"Description: {project.description}\n"
                result += f"State: {project.state}\n"
                result += f"Visibility: {project.visibility}\n"
                result += f"URL: {project.url}\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error retrieving projects: {str(e)}"
    
    def get_identity_ids(self, unique_names: List[str]) -> str:
        """Retrieve Azure DevOps identity IDs for a list of unique names"""
        try:
            result = f"Identity IDs for {len(unique_names)} users:\n\n"
            
            for name in unique_names:
                try:
                    # Search for identity
                    identities = self.core_client.get_identities(
                        search_filter='General',
                        filter_value=name
                    )
                    
                    if identities:
                        identity = identities[0]
                        result += f"Name: {name}\n"
                        result += f"ID: {identity.id}\n"
                        result += f"Display Name: {identity.display_name}\n"
                        result += f"Unique Name: {identity.unique_name if hasattr(identity, 'unique_name') else 'N/A'}\n"
                        result += "---\n"
                    else:
                        result += f"Name: {name} - Not found\n---\n"
                except:
                    result += f"Name: {name} - Error retrieving\n---\n"
            
            return result
        except Exception as e:
            return f"Error retrieving identity IDs: {str(e)}"
    
    # ========== Work ==========
    
    def list_team_iterations(self, team_name: str) -> str:
        """Retrieve iterations for a team"""
        try:
            team_context = TeamContext(project=self.project_name, team=team_name)
            iterations = self.work_client.get_team_iterations(team_context=team_context)
            
            if not iterations:
                return f"No iterations found for team '{team_name}'"
            
            result = f"Found {len(iterations)} iterations for team '{team_name}':\n\n"
            for iteration in iterations:
                result += f"ID: {iteration.id}\n"
                result += f"Name: {iteration.name}\n"
                result += f"Path: {iteration.path}\n"
                if iteration.attributes:
                    result += f"Start Date: {iteration.attributes.start_date}\n"
                    result += f"Finish Date: {iteration.attributes.finish_date}\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error retrieving iterations: {str(e)}"
    
    def create_iterations(self, iteration_name: str, start_date: str, 
                         finish_date: str, path: str = None) -> str:
        """Create new iterations in the project"""
        try:
            # Use work item tracking client to create iteration path
            full_path = f"{self.project_name}\\Iteration"
            if path:
                full_path += f"\\{path}"
            full_path += f"\\{iteration_name}"
            
            iteration = {
                "name": iteration_name,
                "attributes": {
                    "startDate": start_date,
                    "finishDate": finish_date
                }
            }
            
            # Note: Creating iterations requires classification nodes API
            result = f"Iteration creation requested:\n"
            result += f"Name: {iteration_name}\n"
            result += f"Start: {start_date}\n"
            result += f"Finish: {finish_date}\n"
            result += f"Path: {full_path}\n"
            result += "\nNote: Iteration creation may require additional API configuration."
            
            return result
        except Exception as e:
            return f"Error creating iteration: {str(e)}"
    
    def assign_iterations(self, team_name: str, iteration_path: str) -> str:
        """Assign existing iterations to a team"""
        try:
            team_context = TeamContext(project=self.project_name, team=team_name)
            
            iteration = TeamSettingsIteration()
            iteration.id = iteration_path
            
            assigned = self.work_client.post_team_iteration(
                iteration=iteration,
                team_context=team_context
            )
            
            return f"Successfully assigned iteration '{iteration_path}' to team '{team_name}'\n" \
                   f"ID: {assigned.id}\n" \
                   f"Name: {assigned.name}"
        except Exception as e:
            return f"Error assigning iteration: {str(e)}"


def create_azdo_additional_services_tools(
    organization_url: str = organization_url,
    personal_access_token: str = personal_access_token,
    project_name: str = project_name
) -> List[Tool]:
    """
    Create LangChain tools for Azure DevOps Additional Services
    (Advanced Security, Test Plans, Wiki, Search, Core, Work)
    
    Returns:
        List of LangChain Tool objects
    """
    connector = AzureDevOpsAdditionalServicesConnector(
        organization_url=organization_url,
        personal_access_token=personal_access_token,
        project_name=project_name
    )
    
    tools = [
        # ========== Advanced Security ==========
        Tool(
            name="advsec_get_alerts",
            func=lambda input_str: connector.get_alerts(
                **eval(input_str) if input_str.strip() else {}
            ),
            description=(
                "Retrieve Advanced Security alerts for a repository. Input should be a Python dict string with keys: "
                "repository_id (required, string), criteria (optional, dict). "
                "Example: \"{'repository_id': 'my-repo'}\""
            )
        ),
        
        Tool(
            name="advsec_get_alert_details",
            func=lambda input_str: connector.get_alert_details(
                **eval(input_str)
            ),
            description=(
                "Get detailed information about a specific Advanced Security alert. Input should be a Python dict string with keys: "
                "repository_id (required, string), alert_id (required, integer). "
                "Example: \"{'repository_id': 'my-repo', 'alert_id': 123}\""
            )
        ),
        
        # ========== Test Plans ==========
        Tool(
            name="testplan_create_test_plan",
            func=lambda input_str: connector.create_test_plan(
                **eval(input_str)
            ),
            description=(
                "Create a new test plan. Input should be a Python dict string with keys: "
                "name (required, string), area_path (optional, string), iteration_path (optional, string), "
                "description (optional, string). "
                "Example: \"{'name': 'Sprint 1 Tests', 'area_path': 'Project\\Area', 'description': 'Test plan for sprint 1'}\""
            )
        ),
        
        Tool(
            name="testplan_create_test_case",
            func=lambda input_str: connector.create_test_case(
                **eval(input_str)
            ),
            description=(
                "Create a new test case work item. Input should be a Python dict string with keys: "
                "title (required, string), steps (optional, list of dicts with 'action' and 'expected' keys), "
                "area_path (optional, string), priority (optional, integer, default 2). "
                "Example: \"{'title': 'Login Test', 'steps': [{'action': 'Enter username', 'expected': 'Username accepted'}], 'priority': 1}\""
            )
        ),
        
        Tool(
            name="testplan_update_test_case_steps",
            func=lambda input_str: connector.update_test_case_steps(
                **eval(input_str)
            ),
            description=(
                "Update an existing test case's steps. Input should be a Python dict string with keys: "
                "test_case_id (required, integer), steps (required, list of dicts with 'action' and 'expected' keys). "
                "Example: \"{'test_case_id': 123, 'steps': [{'action': 'Click button', 'expected': 'Page loads'}]}\""
            )
        ),
        
        Tool(
            name="testplan_add_test_cases_to_suite",
            func=lambda input_str: connector.add_test_cases_to_suite(
                **eval(input_str)
            ),
            description=(
                "Add existing test cases to a test suite. Input should be a Python dict string with keys: "
                "plan_id (required, integer), suite_id (required, integer), test_case_ids (required, list of integers). "
                "Example: \"{'plan_id': 1, 'suite_id': 2, 'test_case_ids': [123, 456, 789]}\""
            )
        ),
        
        Tool(
            name="testplan_list_test_plans",
            func=lambda input_str: connector.list_test_plans(
                **eval(input_str) if input_str.strip() else {}
            ),
            description=(
                "Retrieve a paginated list of test plans. Input should be a Python dict string with keys: "
                "active_only (optional, boolean, default True), detailed (optional, boolean, default False). "
                "Example: \"{'active_only': True, 'detailed': True}\" or \"{}\" for active plans"
            )
        ),
        
        Tool(
            name="testplan_list_test_cases",
            func=lambda input_str: connector.list_test_cases(
                **eval(input_str)
            ),
            description=(
                "Get test cases in a test plan. Input should be a Python dict string with keys: "
                "plan_id (required, integer), suite_id (optional, integer - if not provided, returns all test cases). "
                "Example: \"{'plan_id': 1, 'suite_id': 2}\" or \"{'plan_id': 1}\""
            )
        ),
        
        Tool(
            name="testplan_show_test_results_from_build_id",
            func=lambda build_id: connector.show_test_results_from_build_id(int(build_id)),
            description=(
                "Get test results for a given build ID. Input should be the build ID (integer). "
                "Returns summary and detailed results."
            )
        ),
        
        Tool(
            name="testplan_create_test_suite",
            func=lambda input_str: connector.create_test_suite(
                **eval(input_str)
            ),
            description=(
                "Create a new test suite in a test plan. Input should be a Python dict string with keys: "
                "plan_id (required, integer), suite_name (required, string), "
                "parent_suite_id (optional, integer), suite_type (optional, string, default 'StaticTestSuite'). "
                "Example: \"{'plan_id': 1, 'suite_name': 'Regression Tests', 'suite_type': 'StaticTestSuite'}\""
            )
        ),
        
        # ========== Wiki ==========
        Tool(
            name="wiki_list_wikis",
            func=lambda x: connector.list_wikis(),
            description="Retrieve a list of wikis for the project. No input required."
        ),
        
        Tool(
            name="wiki_get_wiki",
            func=lambda wiki_identifier: connector.get_wiki(wiki_identifier),
            description="Get wiki by identifier. Input should be the wiki ID or name (string)."
        ),
        
        Tool(
            name="wiki_list_pages",
            func=lambda input_str: connector.list_pages(
                **eval(input_str)
            ),
            description=(
                "Retrieve wiki pages for a specific wiki. Input should be a Python dict string with keys: "
                "wiki_identifier (required, string), path (optional, string, default '/'). "
                "Example: \"{'wiki_identifier': 'MyWiki', 'path': '/Documentation'}\""
            )
        ),
        
        Tool(
            name="wiki_get_page",
            func=lambda input_str: connector.get_page(
                **eval(input_str)
            ),
            description=(
                "Retrieve wiki page metadata by path. Input should be a Python dict string with keys: "
                "wiki_identifier (required, string), page_path (required, string). "
                "Example: \"{'wiki_identifier': 'MyWiki', 'page_path': '/Getting-Started'}\""
            )
        ),
        
        Tool(
            name="wiki_get_page_content",
            func=lambda input_str: connector.get_page_content(
                **eval(input_str)
            ),
            description=(
                "Retrieve wiki page content by path. Input should be a Python dict string with keys: "
                "wiki_identifier (required, string), page_path (required, string). "
                "Example: \"{'wiki_identifier': 'MyWiki', 'page_path': '/Getting-Started'}\""
            )
        ),
        
        Tool(
            name="wiki_create_or_update_page",
            func=lambda input_str: connector.create_or_update_page(
                **eval(input_str)
            ),
            description=(
                "Create or update wiki pages with full content support. Input should be a Python dict string with keys: "
                "wiki_identifier (required, string), page_path (required, string), "
                "content (required, string - markdown content), comment (optional, string - commit message). "
                "Example: \"{'wiki_identifier': 'MyWiki', 'page_path': '/New-Page', "
                "'content': '# Title\\\\nContent here', 'comment': 'Initial version'}\""
            )
        ),
        
        # ========== Search ==========
        Tool(
            name="search_code",
            func=lambda input_str: connector.search_code(
                **eval(input_str) if isinstance(eval(input_str), dict) else {'search_text': input_str}
            ),
            description=(
                "Get code search results. Input should be a Python dict string with keys: "
                "search_text (required, string), top (optional, integer, default 50). "
                "Example: \"{'search_text': 'function myFunc', 'top': 20}\" or just \"'myFunc'\""
            )
        ),
        
        Tool(
            name="search_wiki",
            func=lambda input_str: connector.search_wiki(
                **eval(input_str) if isinstance(eval(input_str), dict) else {'search_text': input_str}
            ),
            description=(
                "Get wiki search results. Input should be a Python dict string with keys: "
                "search_text (required, string), top (optional, integer, default 50). "
                "Example: \"{'search_text': 'installation guide', 'top': 20}\" or just \"'installation'\""
            )
        ),
        
        Tool(
            name="search_workitem",
            func=lambda input_str: connector.search_workitem(
                **eval(input_str) if isinstance(eval(input_str), dict) else {'search_text': input_str}
            ),
            description=(
                "Get work item search results. Input should be a Python dict string with keys: "
                "search_text (required, string), top (optional, integer, default 50). "
                "Example: \"{'search_text': 'bug authentication', 'top': 20}\" or just \"'authentication'\""
            )
        ),
        
        # ========== Core ==========
        Tool(
            name="core_list_project_teams",
            func=lambda x: connector.list_project_teams(),
            description="Retrieve a list of teams for the configured project. No input required."
        ),
        
        Tool(
            name="core_list_projects",
            func=lambda x: connector.list_projects(),
            description="Retrieve a list of projects in the Azure DevOps organization. No input required."
        ),
        
        Tool(
            name="core_get_identity_ids",
            func=lambda input_str: connector.get_identity_ids(
                eval(input_str) if isinstance(eval(input_str), list) else [str(input_str)]
            ),
            description=(
                "Retrieve Azure DevOps identity IDs for a list of unique names. "
                "Input can be either a JSON array of usernames/emails OR a single string. "
                "For multiple users, use format: [\"user1@contoso.com\", \"user2@contoso.com\"]. "
                "For single user, use format: \"user1@contoso.com\". "
                "Examples: [\"john@contoso.com\", \"jane@contoso.com\"] or \"john@contoso.com\""
            )
        ),
        
        # ========== Work ==========
        Tool(
            name="work_list_team_iterations",
            func=lambda team_name: connector.list_team_iterations(team_name),
            description=(
                "Retrieve iterations for a specific team. Input should be the team name (string). "
                "Returns iteration details including dates."
            )
        ),
        
        Tool(
            name="work_create_iterations",
            func=lambda input_str: connector.create_iterations(
                **eval(input_str)
            ),
            description=(
                "Create new iterations in the project. Input should be a Python dict string with keys: "
                "iteration_name (required, string), start_date (required, ISO date string), "
                "finish_date (required, ISO date string), path (optional, string - parent path). "
                "Example: \"{'iteration_name': 'Sprint 1', 'start_date': '2025-01-01', 'finish_date': '2025-01-14'}\""
            )
        ),
        
        Tool(
            name="work_assign_iterations",
            func=lambda input_str: connector.assign_iterations(
                **eval(input_str)
            ),
            description=(
                "Assign existing iterations to a specific team. Input should be a Python dict string with keys: "
                "team_name (required, string), iteration_path (required, string - full iteration path). "
                "Example: \"{'team_name': 'Team A', 'iteration_path': 'Project\\\\Iteration\\\\Sprint 1'}\""
            )
        ),
    ]
    
    return tools


# Example usage
# if __name__ == "__main__":
#     # Create the tools
#     tools = create_azdo_additional_services_tools()
    
#     print(f"Created {len(tools)} Azure DevOps Additional Services tools:")
    
#     # Group tools by category
#     categories = {
#         'Advanced Security': [t for t in tools if t.name.startswith('advsec_')],
#         'Test Plans': [t for t in tools if t.name.startswith('testplan_')],
#         'Wiki': [t for t in tools if t.name.startswith('wiki_')],
#         'Search': [t for t in tools if t.name.startswith('search_')],
#         'Core': [t for t in tools if t.name.startswith('core_')],
#         'Work': [t for t in tools if t.name.startswith('work_')],
#     }
    
#     for category, category_tools in categories.items():
#         print(f"\n{category} ({len(category_tools)} tools):")
#         for tool in category_tools:
#             print(f"  - {tool.name}")