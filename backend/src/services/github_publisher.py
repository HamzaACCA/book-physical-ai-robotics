"""GitHub repository publisher service."""

import base64
import subprocess
from pathlib import Path
from typing import Optional

import httpx

from backend.src.core.config import settings
from backend.src.core.logging import get_logger

logger = get_logger(__name__)


class GitHubPublisher:
    """Publish Docusaurus projects to GitHub."""

    def __init__(self, github_token: str, github_username: str):
        """Initialize GitHub publisher.

        Args:
            github_token: GitHub personal access token
            github_username: GitHub username
        """
        self.token = github_token
        self.username = github_username
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    async def create_repository(
        self,
        repo_name: str,
        description: str = "",
        private: bool = False
    ) -> dict:
        """Create a new GitHub repository.

        Args:
            repo_name: Repository name
            description: Repository description
            private: Whether repository should be private

        Returns:
            Repository data from GitHub API
        """
        logger.info(f"Creating GitHub repository: {repo_name}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/user/repos",
                headers=self.headers,
                json={
                    "name": repo_name,
                    "description": description,
                    "private": private,
                    "auto_init": False
                },
                timeout=30.0
            )

            if response.status_code == 201:
                repo_data = response.json()
                logger.info(f"Repository created: {repo_data['html_url']}")
                return repo_data
            elif response.status_code == 422:
                # Repository already exists
                logger.warning(f"Repository {repo_name} already exists")
                # Get existing repository
                get_response = await client.get(
                    f"{self.base_url}/repos/{self.username}/{repo_name}",
                    headers=self.headers
                )
                if get_response.status_code == 200:
                    return get_response.json()
                raise Exception(f"Repository exists but couldn't fetch it: {get_response.text}")
            else:
                raise Exception(f"Failed to create repository: {response.status_code} - {response.text}")

    async def push_to_github(
        self,
        project_dir: Path,
        repo_name: str,
        commit_message: str = "Initial commit from Book Creator"
    ) -> None:
        """Push project files to GitHub repository using git commands.

        Args:
            project_dir: Path to project directory
            repo_name: Repository name
            commit_message: Git commit message
        """
        logger.info(f"Pushing {project_dir} to GitHub repository {repo_name}")

        repo_url = f"https://{self.token}@github.com/{self.username}/{repo_name}.git"

        try:
            # Initialize git repository
            subprocess.run(
                ["git", "init"],
                cwd=project_dir,
                check=True,
                capture_output=True
            )

            # Configure git user
            subprocess.run(
                ["git", "config", "user.name", "Book Creator Bot"],
                cwd=project_dir,
                check=True,
                capture_output=True
            )
            subprocess.run(
                ["git", "config", "user.email", "bot@bookcreator.ai"],
                cwd=project_dir,
                check=True,
                capture_output=True
            )

            # Add all files
            subprocess.run(
                ["git", "add", "."],
                cwd=project_dir,
                check=True,
                capture_output=True
            )

            # Commit
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=project_dir,
                check=True,
                capture_output=True
            )

            # Add remote
            subprocess.run(
                ["git", "remote", "add", "origin", repo_url],
                cwd=project_dir,
                check=True,
                capture_output=True
            )

            # Push to main branch
            subprocess.run(
                ["git", "push", "-u", "origin", "main"],
                cwd=project_dir,
                check=True,
                capture_output=True
            )

            logger.info(f"Successfully pushed to {self.username}/{repo_name}")

        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e.stderr.decode()}")
            raise Exception(f"Failed to push to GitHub: {e.stderr.decode()}")

    async def enable_github_pages(self, repo_name: str) -> dict:
        """Enable GitHub Pages for repository.

        Args:
            repo_name: Repository name

        Returns:
            Pages configuration data
        """
        logger.info(f"Enabling GitHub Pages for {repo_name}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/repos/{self.username}/{repo_name}/pages",
                headers=self.headers,
                json={
                    "source": {
                        "branch": "gh-pages",
                        "path": "/"
                    }
                },
                timeout=30.0
            )

            if response.status_code in [201, 409]:  # 409 = already exists
                logger.info("GitHub Pages enabled successfully")
                # Get pages info
                get_response = await client.get(
                    f"{self.base_url}/repos/{self.username}/{repo_name}/pages",
                    headers=self.headers
                )
                if get_response.status_code == 200:
                    return get_response.json()
                return {"status": "enabled"}
            else:
                logger.warning(f"Failed to enable Pages: {response.status_code} - {response.text}")
                return {"status": "pending"}

    async def get_latest_workflow_run(self, repo_name: str) -> Optional[dict]:
        """Get the latest GitHub Actions workflow run.

        Args:
            repo_name: Repository name

        Returns:
            Workflow run data or None
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{self.username}/{repo_name}/actions/runs?per_page=1",
                headers=self.headers,
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()
                runs = data.get("workflow_runs", [])
                if runs:
                    return runs[0]
            return None

    async def publish_book(
        self,
        project_dir: Path,
        repo_name: str,
        title: str,
        description: str = ""
    ) -> tuple[str, str]:
        """Complete publishing workflow: create repo, push code, enable Pages.

        Args:
            project_dir: Path to Docusaurus project
            repo_name: Repository name
            title: Book title
            description: Repository description

        Returns:
            Tuple of (repo_url, pages_url)
        """
        logger.info(f"Publishing book '{title}' to GitHub")

        # Create repository
        repo_data = await self.create_repository(
            repo_name=repo_name,
            description=description or f"Book: {title}"
        )
        repo_url = repo_data["html_url"]

        # Push code
        await self.push_to_github(
            project_dir=project_dir,
            repo_name=repo_name,
            commit_message=f"📚 Initial commit: {title}"
        )

        # Enable GitHub Pages
        await self.enable_github_pages(repo_name)

        # Construct pages URL
        pages_url = f"https://{self.username}.github.io/{repo_name}/"

        logger.info(f"Book published successfully: {pages_url}")
        return repo_url, pages_url
