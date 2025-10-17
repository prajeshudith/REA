import os
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv
from langchain.tools import Tool
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from azure.devops.v7_0.git.models import (
    GitPullRequest,
    GitPullRequestSearchCriteria,
    GitQueryCommitsCriteria,
    Comment,
    CommentThread,
    CommentThreadContext,
    CommentPosition,
    IdentityRefWithVote,
    GitRefUpdate,
    GitRef
)
import json

load_dotenv()

# Configuration
organization_url = os.getenv('AZURE_ORG_URL', 'https://dev.azure.com/yourorg')
personal_access_token = os.getenv('AZURE_DEVOPS_PERSONAL_ACCESS_TOKEN', 'your-pat-token')
project_name = os.getenv('PROJECT_NAME', 'YourProject')


class AzureDevOpsRepositoriesConnector:
    """Azure DevOps Repositories Connector using PAT authentication"""
    
    def __init__(self, organization_url: str, personal_access_token: str, project_name: str):
        self.organization_url = organization_url
        self.project_name = project_name
        credentials = BasicAuthentication('', personal_access_token)
        self.connection = Connection(base_url=organization_url, creds=credentials)
        self.git_client = self.connection.clients.get_git_client()
    
    def list_repos_by_project(self) -> str:
        """Retrieve a list of repositories for a given project"""
        try:
            repos = self.git_client.get_repositories(project=self.project_name)
            
            if not repos:
                return f"No repositories found in project '{self.project_name}'"
            
            result = f"Found {len(repos)} repositories in project '{self.project_name}':\n\n"
            for repo in repos:
                result += f"Name: {repo.name}\n"
                result += f"ID: {repo.id}\n"
                result += f"URL: {repo.remote_url}\n"
                result += f"Default Branch: {repo.default_branch}\n"
                result += f"Size: {repo.size} bytes\n"
                result += f"Web URL: {repo.web_url}\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error retrieving repositories: {str(e)}"
    
    def list_pull_requests_by_repo_or_project(self, repository_id: str = None, 
                                               status: str = "active") -> str:
        """Retrieve a list of pull requests for a given repository or project"""
        try:
            # Create search criteria
            search_criteria = GitPullRequestSearchCriteria()
            if status.lower() == "active":
                search_criteria.status = "active"
            elif status.lower() == "completed":
                search_criteria.status = "completed"
            elif status.lower() == "abandoned":
                search_criteria.status = "abandoned"
            elif status.lower() == "all":
                search_criteria.status = "all"
            
            if repository_id:
                # Get PRs for specific repository
                pull_requests = self.git_client.get_pull_requests(
                    repository_id=repository_id,
                    search_criteria=search_criteria,
                    project=self.project_name
                )
                scope = f"repository '{repository_id}'"
            else:
                # Get PRs for entire project
                pull_requests = self.git_client.get_pull_requests_by_project(
                    project=self.project_name,
                    search_criteria=search_criteria
                )
                scope = f"project '{self.project_name}'"
            
            if not pull_requests:
                return f"No pull requests found in {scope} with status '{status}'"
            
            result = f"Found {len(pull_requests)} pull requests in {scope}:\n\n"
            for pr in pull_requests:
                result += f"PR #{pr.pull_request_id}: {pr.title}\n"
                result += f"Status: {pr.status}\n"
                result += f"Created By: {pr.created_by.display_name}\n"
                result += f"Source: {pr.source_ref_name} -> Target: {pr.target_ref_name}\n"
                result += f"Created: {pr.creation_date}\n"
                result += f"URL: {pr.url}\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error retrieving pull requests: {str(e)}"
    
    def list_branches_by_repo(self, repository_id: str) -> str:
        """Retrieve a list of branches for a given repository"""
        try:
            refs = self.git_client.get_refs(
                repository_id=repository_id,
                project=self.project_name,
                filter="heads/"
            )
            
            if not refs:
                return f"No branches found in repository '{repository_id}'"
            
            result = f"Found {len(refs)} branches in repository '{repository_id}':\n\n"
            for ref in refs:
                branch_name = ref.name.replace("refs/heads/", "")
                result += f"Branch: {branch_name}\n"
                result += f"Object ID: {ref.object_id}\n"
                result += f"Creator: {ref.creator.display_name if ref.creator else 'Unknown'}\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error retrieving branches: {str(e)}"
    
    def list_my_branches_by_repo(self, repository_id: str) -> str:
        """Retrieve a list of your branches for a given repository"""
        try:
            # Get current user's identity
            connection_data = self.connection.get_connection_data()
            user_id = connection_data.authenticated_user.id
            
            refs = self.git_client.get_refs(
                repository_id=repository_id,
                project=self.project_name,
                filter="heads/"
            )
            
            # Filter branches created by current user
            my_branches = [ref for ref in refs if ref.creator and ref.creator.id == user_id]
            
            if not my_branches:
                return f"No branches found created by you in repository '{repository_id}'"
            
            result = f"Found {len(my_branches)} branches created by you:\n\n"
            for ref in my_branches:
                branch_name = ref.name.replace("refs/heads/", "")
                result += f"Branch: {branch_name}\n"
                result += f"Object ID: {ref.object_id}\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error retrieving your branches: {str(e)}"
    
    def list_pull_requests_by_commits(self, repository_id: str, commit_ids: List[str]) -> str:
        """List pull requests associated with commits"""
        try:
            all_prs = []
            
            for commit_id in commit_ids:
                prs = self.git_client.get_pull_request_by_id(
                    project=self.project_name,
                    pull_request_id=commit_id
                )
                if prs:
                    all_prs.extend(prs if isinstance(prs, list) else [prs])
            
            if not all_prs:
                return f"No pull requests found for the specified commits"
            
            result = f"Found {len(all_prs)} pull requests:\n\n"
            for pr in all_prs:
                result += f"PR #{pr.pull_request_id}: {pr.title}\n"
                result += f"Status: {pr.status}\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error retrieving pull requests by commits: {str(e)}"
    
    def list_pull_request_threads(self, repository_id: str, pull_request_id: int) -> str:
        """Retrieve a list of comment threads for a pull request"""
        try:
            threads = self.git_client.get_threads(
                repository_id=repository_id,
                pull_request_id=pull_request_id,
                project=self.project_name
            )
            
            if not threads:
                return f"No comment threads found for PR #{pull_request_id}"
            
            result = f"Found {len(threads)} comment threads for PR #{pull_request_id}:\n\n"
            for thread in threads:
                result += f"Thread ID: {thread.id}\n"
                result += f"Status: {thread.status}\n"
                result += f"Published Date: {thread.published_date}\n"
                if thread.comments:
                    result += f"Comments: {len(thread.comments)}\n"
                    result += f"First Comment: {thread.comments[0].content[:100]}...\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error retrieving PR threads: {str(e)}"
    
    def list_pull_request_thread_comments(self, repository_id: str, 
                                          pull_request_id: int, thread_id: int) -> str:
        """Retrieve a list of comments in a pull request thread"""
        try:
            comments = self.git_client.get_comments(
                repository_id=repository_id,
                pull_request_id=pull_request_id,
                thread_id=thread_id,
                project=self.project_name
            )
            
            if not comments:
                return f"No comments found in thread #{thread_id}"
            
            result = f"Found {len(comments)} comments in thread #{thread_id}:\n\n"
            for comment in comments:
                result += f"Comment ID: {comment.id}\n"
                result += f"Author: {comment.author.display_name if comment.author else 'Unknown'}\n"
                result += f"Published: {comment.published_date}\n"
                result += f"Content: {comment.content}\n"
                result += f"Comment Type: {comment.comment_type}\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error retrieving thread comments: {str(e)}"
    
    def get_repo_by_name_or_id(self, repository_name_or_id: str) -> str:
        """Get the repository by project and repository name or ID"""
        try:
            repo = self.git_client.get_repository(
                repository_id=repository_name_or_id,
                project=self.project_name
            )
            
            result = f"Repository Details:\n\n"
            result += f"Name: {repo.name}\n"
            result += f"ID: {repo.id}\n"
            result += f"URL: {repo.remote_url}\n"
            result += f"Web URL: {repo.web_url}\n"
            result += f"Default Branch: {repo.default_branch}\n"
            result += f"Size: {repo.size} bytes\n"
            result += f"Is Disabled: {repo.is_disabled}\n"
            result += f"Project: {repo.project.name}\n"
            
            return result
        except Exception as e:
            return f"Error retrieving repository: {str(e)}"
    
    def get_branch_by_name(self, repository_id: str, branch_name: str) -> str:
        """Get a branch by its name"""
        try:
            # Ensure branch name has proper prefix
            if not branch_name.startswith("refs/heads/"):
                branch_name = f"refs/heads/{branch_name}"
            
            branch = self.git_client.get_branch(
                repository_id=repository_id,
                name=branch_name,
                project=self.project_name
            )
            
            result = f"Branch Details:\n\n"
            result += f"Name: {branch.name.replace('refs/heads/', '')}\n"
            result += f"Object ID: {branch.object_id}\n"
            result += f"Creator: {branch.creator.display_name if branch.creator else 'Unknown'}\n"
            result += f"URL: {branch.url}\n"
            
            # Get commit details
            if branch.object_id:
                commit = self.git_client.get_commit(
                    commit_id=branch.object_id,
                    repository_id=repository_id,
                    project=self.project_name
                )
                result += f"\nLatest Commit:\n"
                result += f"  Commit ID: {commit.commit_id}\n"
                result += f"  Author: {commit.author.name}\n"
                result += f"  Date: {commit.author.date}\n"
                result += f"  Comment: {commit.comment}\n"
            
            return result
        except Exception as e:
            return f"Error retrieving branch: {str(e)}"
    
    def get_pull_request_by_id(self, repository_id: str, pull_request_id: int) -> str:
        """Get a pull request by its ID"""
        try:
            pr = self.git_client.get_pull_request(
                repository_id=repository_id,
                pull_request_id=pull_request_id,
                project=self.project_name
            )
            
            result = f"Pull Request Details:\n\n"
            result += f"PR #{pr.pull_request_id}: {pr.title}\n"
            result += f"Description: {pr.description}\n"
            result += f"Status: {pr.status}\n"
            result += f"Created By: {pr.created_by.display_name}\n"
            result += f"Created Date: {pr.creation_date}\n"
            result += f"Source Branch: {pr.source_ref_name}\n"
            result += f"Target Branch: {pr.target_ref_name}\n"
            result += f"Merge Status: {pr.merge_status}\n"
            result += f"Is Draft: {pr.is_draft}\n"
            result += f"URL: {pr.url}\n"
            
            if pr.reviewers:
                result += f"\nReviewers ({len(pr.reviewers)}):\n"
                for reviewer in pr.reviewers:
                    vote_text = {0: "No Vote", 10: "Approved", 5: "Approved with suggestions", 
                                -5: "Waiting for author", -10: "Rejected"}.get(reviewer.vote, "Unknown")
                    result += f"  - {reviewer.display_name}: {vote_text}\n"
            
            return result
        except Exception as e:
            return f"Error retrieving pull request: {str(e)}"
    
    def create_pull_request(self, repository_id: str, source_branch: str, 
                           target_branch: str, title: str, description: str = "",
                           is_draft: bool = False, reviewers: List[str] = None) -> str:
        """Create a new pull request"""
        try:
            # Ensure branch names have proper format
            if not source_branch.startswith("refs/heads/"):
                source_branch = f"refs/heads/{source_branch}"
            if not target_branch.startswith("refs/heads/"):
                target_branch = f"refs/heads/{target_branch}"
            
            # Create PR object
            pr = GitPullRequest(
                source_ref_name=source_branch,
                target_ref_name=target_branch,
                title=title,
                description=description,
                is_draft=is_draft
            )
            
            # Add reviewers if provided
            if reviewers:
                pr.reviewers = [IdentityRefWithVote(id=reviewer_id) for reviewer_id in reviewers]
            
            created_pr = self.git_client.create_pull_request(
                git_pull_request_to_create=pr,
                repository_id=repository_id,
                project=self.project_name
            )
            
            return f"Successfully created Pull Request #{created_pr.pull_request_id}\n" \
                   f"Title: {created_pr.title}\n" \
                   f"Source: {created_pr.source_ref_name} -> Target: {created_pr.target_ref_name}\n" \
                   f"URL: {created_pr.url}"
        except Exception as e:
            return f"Error creating pull request: {str(e)}"
    
    def create_branch(self, repository_id: str, branch_name: str, 
                     base_commit_id: str) -> str:
        """Create a new branch in the repository"""
        try:
            # Ensure branch name has proper format
            if not branch_name.startswith("refs/heads/"):
                branch_name = f"refs/heads/{branch_name}"
            
            # Create ref update
            ref_update = GitRefUpdate(
                name=branch_name,
                old_object_id="0000000000000000000000000000000000000000",
                new_object_id=base_commit_id
            )
            
            result = self.git_client.update_refs(
                ref_updates=[ref_update],
                repository_id=repository_id,
                project=self.project_name
            )
            
            if result and len(result) > 0:
                return f"Successfully created branch '{branch_name.replace('refs/heads/', '')}'\n" \
                       f"Base Commit: {base_commit_id}\n" \
                       f"Update Status: {result[0].update_status}"
            else:
                return f"Branch creation completed but no result returned"
        except Exception as e:
            return f"Error creating branch: {str(e)}"
    
    def update_pull_request(self, repository_id: str, pull_request_id: int,
                           title: str = None, description: str = None,
                           is_draft: bool = None, target_branch: str = None) -> str:
        """Update various fields of an existing pull request"""
        try:
            # Get existing PR
            existing_pr = self.git_client.get_pull_request(
                repository_id=repository_id,
                pull_request_id=pull_request_id,
                project=self.project_name
            )
            
            # Create update object
            pr_update = GitPullRequest()
            
            if title is not None:
                pr_update.title = title
            if description is not None:
                pr_update.description = description
            if is_draft is not None:
                pr_update.is_draft = is_draft
            if target_branch is not None:
                if not target_branch.startswith("refs/heads/"):
                    target_branch = f"refs/heads/{target_branch}"
                pr_update.target_ref_name = target_branch
            
            updated_pr = self.git_client.update_pull_request(
                git_pull_request_to_update=pr_update,
                repository_id=repository_id,
                pull_request_id=pull_request_id,
                project=self.project_name
            )
            
            return f"Successfully updated PR #{pull_request_id}\n" \
                   f"Title: {updated_pr.title}\n" \
                   f"Status: {updated_pr.status}\n" \
                   f"Is Draft: {updated_pr.is_draft}"
        except Exception as e:
            return f"Error updating pull request: {str(e)}"
    
    def update_pull_request_reviewers(self, repository_id: str, pull_request_id: int,
                                      add_reviewers: List[str] = None,
                                      remove_reviewers: List[str] = None) -> str:
        """Add or remove reviewers for an existing pull request"""
        try:
            results = []
            
            # Add reviewers
            if add_reviewers:
                for reviewer_id in add_reviewers:
                    reviewer = IdentityRefWithVote(id=reviewer_id)
                    self.git_client.create_pull_request_reviewer(
                        reviewer=reviewer,
                        repository_id=repository_id,
                        pull_request_id=pull_request_id,
                        reviewer_id=reviewer_id,
                        project=self.project_name
                    )
                    results.append(f"Added reviewer: {reviewer_id}")
            
            # Remove reviewers
            if remove_reviewers:
                for reviewer_id in remove_reviewers:
                    self.git_client.delete_pull_request_reviewer(
                        repository_id=repository_id,
                        pull_request_id=pull_request_id,
                        reviewer_id=reviewer_id,
                        project=self.project_name
                    )
                    results.append(f"Removed reviewer: {reviewer_id}")
            
            return f"Successfully updated reviewers for PR #{pull_request_id}:\n" + "\n".join(results)
        except Exception as e:
            return f"Error updating reviewers: {str(e)}"
    
    def reply_to_comment(self, repository_id: str, pull_request_id: int,
                        thread_id: int, comment_text: str) -> str:
        """Reply to a specific comment on a pull request"""
        try:
            comment = Comment(content=comment_text, comment_type=1)
            
            created_comment = self.git_client.create_comment(
                comment=comment,
                repository_id=repository_id,
                pull_request_id=pull_request_id,
                thread_id=thread_id,
                project=self.project_name
            )
            
            return f"Successfully added reply to thread #{thread_id}\n" \
                   f"Comment ID: {created_comment.id}\n" \
                   f"Content: {created_comment.content}"
        except Exception as e:
            return f"Error replying to comment: {str(e)}"
    
    def resolve_comment(self, repository_id: str, pull_request_id: int,
                       thread_id: int) -> str:
        """Resolve a specific comment thread on a pull request"""
        try:
            # Get the thread
            thread = self.git_client.get_pull_request_thread(
                repository_id=repository_id,
                pull_request_id=pull_request_id,
                thread_id=thread_id,
                project=self.project_name
            )
            
            # Update thread status to fixed
            thread.status = 4  # 4 = Fixed/Resolved
            
            updated_thread = self.git_client.update_thread(
                comment_thread=thread,
                repository_id=repository_id,
                pull_request_id=pull_request_id,
                thread_id=thread_id,
                project=self.project_name
            )
            
            return f"Successfully resolved thread #{thread_id} in PR #{pull_request_id}"
        except Exception as e:
            return f"Error resolving comment: {str(e)}"
    
    def search_commits(self, repository_id: str, search_text: str = None,
                      author: str = None, from_date: str = None,
                      to_date: str = None, max_results: int = 50) -> str:
        """Search for commits"""
        try:
            search_criteria = GitQueryCommitsCriteria()
            
            if author:
                search_criteria.author = author
            if from_date:
                search_criteria.from_date = from_date
            if to_date:
                search_criteria.to_date = to_date
            if max_results:
                search_criteria.top = max_results
            
            commits = self.git_client.get_commits(
                repository_id=repository_id,
                search_criteria=search_criteria,
                project=self.project_name
            )
            
            if not commits:
                return "No commits found matching the search criteria"
            
            result = f"Found {len(commits)} commits:\n\n"
            for commit in commits:
                result += f"Commit ID: {commit.commit_id[:12]}\n"
                result += f"Author: {commit.author.name}\n"
                result += f"Date: {commit.author.date}\n"
                result += f"Message: {commit.comment}\n"
                result += "---\n"
            
            return result
        except Exception as e:
            return f"Error searching commits: {str(e)}"
    
    def create_pull_request_thread(self, repository_id: str, pull_request_id: int,
                                   comment_text: str, file_path: str = None,
                                   line_number: int = None) -> str:
        """Create a new comment thread on a pull request"""
        try:
            # Create comment
            comment = Comment(content=comment_text, comment_type=1)
            
            # Create thread
            thread = CommentThread()
            thread.comments = [comment]
            thread.status = 1  # Active
            
            # If file path and line provided, add thread context
            if file_path and line_number:
                thread_context = CommentThreadContext()
                thread_context.file_path = file_path
                
                # Add right file position
                right_position = CommentPosition()
                right_position.line = line_number
                right_position.offset = 1
                thread_context.right_file_end = right_position
                thread_context.right_file_start = right_position
                
                thread.thread_context = thread_context
            
            created_thread = self.git_client.create_thread(
                comment_thread=thread,
                repository_id=repository_id,
                pull_request_id=pull_request_id,
                project=self.project_name
            )
            
            return f"Successfully created comment thread #{created_thread.id} on PR #{pull_request_id}\n" \
                   f"Comment: {comment_text}"
        except Exception as e:
            return f"Error creating PR thread: {str(e)}"


def create_azdo_repositories_tools(
    organization_url: str = organization_url,
    personal_access_token: str = personal_access_token,
    project_name: str = project_name
) -> List[Tool]:
    """
    Create LangChain tools for Azure DevOps Repositories operations
    
    Returns:
        List of LangChain Tool objects
    """
    connector = AzureDevOpsRepositoriesConnector(
        organization_url=organization_url,
        personal_access_token=personal_access_token,
        project_name=project_name
    )
    
    tools = [
        Tool(
            name="repo_list_repos_by_project",
            func=lambda x: connector.list_repos_by_project(),
            description="Retrieve a list of repositories for the configured project. No input required."
        ),
        
        Tool(
            name="repo_list_pull_requests_by_repo_or_project",
            func=lambda input_str: connector.list_pull_requests_by_repo_or_project(
                **eval(input_str) if input_str.strip() else {}
            ),
            description=(
                "Retrieve pull requests for a repository or project. Input should be a Python dict string with keys: "
                "repository_id (optional, string), status (optional, one of: 'active', 'completed', 'abandoned', 'all', default 'active'). "
                "Example: \"{'repository_id': 'my-repo', 'status': 'active'}\" or \"{}\" for all PRs in project"
            )
        ),
        
        Tool(
            name="repo_list_branches_by_repo",
            func=lambda repository_id: connector.list_branches_by_repo(repository_id),
            description="Retrieve branches for a repository. Input should be the repository ID or name (string)."
        ),
        
        Tool(
            name="repo_list_my_branches_by_repo",
            func=lambda repository_id: connector.list_my_branches_by_repo(repository_id),
            description="Retrieve your branches for a repository. Input should be the repository ID (string)."
        ),
        
        Tool(
            name="repo_list_pull_requests_by_commits",
            func=lambda input_str: connector.list_pull_requests_by_commits(
                **eval(input_str)
            ),
            description=(
                "List pull requests associated with commits. Input should be a Python dict string with keys: "
                "repository_id (required, string), commit_ids (required, list of commit IDs). "
                "Example: \"{'repository_id': 'my-repo', 'commit_ids': ['abc123', 'def456']}\""
            )
        ),
        
        Tool(
            name="repo_list_pull_request_threads",
            func=lambda input_str: connector.list_pull_request_threads(
                **eval(input_str)
            ),
            description=(
                "Retrieve comment threads for a pull request. Input should be a Python dict string with keys: "
                "repository_id (required, string), pull_request_id (required, integer). "
                "Example: \"{'repository_id': 'my-repo', 'pull_request_id': 123}\""
            )
        ),
        
        Tool(
            name="repo_list_pull_request_thread_comments",
            func=lambda input_str: connector.list_pull_request_thread_comments(
                **eval(input_str)
            ),
            description=(
                "Retrieve comments in a PR thread. Input should be a Python dict string with keys: "
                "repository_id (required, string), pull_request_id (required, integer), thread_id (required, integer). "
                "Example: \"{'repository_id': 'my-repo', 'pull_request_id': 123, 'thread_id': 456}\""
            )
        ),
        
        Tool(
            name="repo_get_repo_by_name_or_id",
            func=lambda repository_name_or_id: connector.get_repo_by_name_or_id(repository_name_or_id),
            description="Get repository details by name or ID. Input should be the repository name or ID (string)."
        ),
        
        Tool(
            name="repo_get_branch_by_name",
            func=lambda input_str: connector.get_branch_by_name(
                **eval(input_str)
            ),
            description=(
                "Get a branch by its name. Input should be a Python dict string with keys: "
                "repository_id (required, string), branch_name (required, string). "
                "Example: \"{'repository_id': 'my-repo', 'branch_name': 'main'}\""
            )
        ),
        
        Tool(
            name="repo_get_pull_request_by_id",
            func=lambda input_str: connector.get_pull_request_by_id(
                **eval(input_str)
            ),
            description=(
                "Get a pull request by its ID. Input should be a Python dict string with keys: "
                "repository_id (required, string), pull_request_id (required, integer). "
                "Example: \"{'repository_id': 'my-repo', 'pull_request_id': 123}\""
            )
        ),
        
        Tool(
            name="repo_create_pull_request",
            func=lambda input_str: connector.create_pull_request(
                **eval(input_str)
            ),
            description=(
                "Create a new pull request. Input should be a Python dict string with keys: "
                "repository_id (required, string), source_branch (required, string), target_branch (required, string), "
                "title (required, string), description (optional, string), is_draft (optional, boolean), "
                "reviewers (optional, list of reviewer IDs). "
                "Example: \"{'repository_id': 'my-repo', 'source_branch': 'feature/new', 'target_branch': 'main', "
                "'title': 'Add new feature', 'description': 'This PR adds...', 'is_draft': False}\""
            )
        ),
        
        Tool(
            name="repo_create_branch",
            func=lambda input_str: connector.create_branch(
                **eval(input_str)
            ),
            description=(
                "Create a new branch in the repository. Input should be a Python dict string with keys: "
                "repository_id (required, string), branch_name (required, string), base_commit_id (required, string - commit SHA). "
                "Example: \"{'repository_id': 'my-repo', 'branch_name': 'feature/new-branch', "
                "'base_commit_id': 'abc123def456...'}\""
            )
        ),
        
        Tool(
            name="repo_update_pull_request",
            func=lambda input_str: connector.update_pull_request(
                **eval(input_str)
            ),
            description=(
                "Update various fields of an existing pull request. Input should be a Python dict string with keys: "
                "repository_id (required, string), pull_request_id (required, integer), "
                "title (optional, string), description (optional, string), is_draft (optional, boolean), "
                "target_branch (optional, string). "
                "Example: \"{'repository_id': 'my-repo', 'pull_request_id': 123, 'title': 'Updated title', 'is_draft': False}\""
            )
        ),
        
        Tool(
            name="repo_update_pull_request_reviewers",
            func=lambda input_str: connector.update_pull_request_reviewers(
                **eval(input_str)
            ),
            description=(
                "Add or remove reviewers for a pull request. Input should be a Python dict string with keys: "
                "repository_id (required, string), pull_request_id (required, integer), "
                "add_reviewers (optional, list of reviewer IDs), remove_reviewers (optional, list of reviewer IDs). "
                "Example: \"{'repository_id': 'my-repo', 'pull_request_id': 123, "
                "'add_reviewers': ['user1@contoso.com'], 'remove_reviewers': ['user2@contoso.com']}\""
            )
        ),
        
        Tool(
            name="repo_reply_to_comment",
            func=lambda input_str: connector.reply_to_comment(
                **eval(input_str)
            ),
            description=(
                "Reply to a specific comment on a pull request. Input should be a Python dict string with keys: "
                "repository_id (required, string), pull_request_id (required, integer), "
                "thread_id (required, integer), comment_text (required, string). "
                "Example: \"{'repository_id': 'my-repo', 'pull_request_id': 123, 'thread_id': 456, "
                "'comment_text': 'I agree with this change'}\""
            )
        ),
        
        Tool(
            name="repo_resolve_comment",
            func=lambda input_str: connector.resolve_comment(
                **eval(input_str)
            ),
            description=(
                "Resolve a specific comment thread on a pull request. Input should be a Python dict string with keys: "
                "repository_id (required, string), pull_request_id (required, integer), thread_id (required, integer). "
                "Example: \"{'repository_id': 'my-repo', 'pull_request_id': 123, 'thread_id': 456}\""
            )
        ),
        
        Tool(
            name="repo_search_commits",
            func=lambda input_str: connector.search_commits(
                **eval(input_str)
            ),
            description=(
                 "Search for commits in a repository. Input MUST be a Python dictionary string with keys: "
                "repository_id (required, string), search_text (optional, string), author (optional, string), "
                "from_date (optional, ISO date string), to_date (optional, ISO date string), max_results (optional, integer, default 50). "
                "Format: {\"repository_id\": \"value\", \"author\": \"value\", \"max_results\": number}. "
                "Example: {\"repository_id\": \"my-repo\", \"author\": \"john@contoso.com\", \"max_results\": 20}"
            )
        ),
        
        Tool(
            name="repo_create_pull_request_thread",
            func=lambda input_str: connector.create_pull_request_thread(
                **eval(input_str)
            ),
            description=(
                "Create a new comment thread on a pull request. Input should be a Python dict string with keys: "
                "repository_id (required, string), pull_request_id (required, integer), comment_text (required, string), "
                "file_path (optional, string - for file-specific comments), line_number (optional, integer - for line-specific comments). "
                "Example: \"{'repository_id': 'my-repo', 'pull_request_id': 123, 'comment_text': 'Please review this', "
                "'file_path': '/src/main.py', 'line_number': 42}\""
            )
        ),
    ]
    
    return tools


# # Example usage
# if __name__ == "__main__":
#     # Create the tools
#     tools = create_azdo_repositories_tools()
    
#     print(f"Created {len(tools)} Azure DevOps Repositories tools:")
#     for tool in tools:
#         print(f"  - {tool.name}: {tool.description[:80]}...")
    
#     # Example: List repositories
#     print("\n=== Example: Listing repositories ===")
#     list_repos_tool = next(t for t in tools if t.name == "repo_list_repos_by_project")
#     result = list_repos_tool.run("")
#     print(result)