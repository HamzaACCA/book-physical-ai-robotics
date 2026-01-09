"""Deployment monitoring service."""

import asyncio
from typing import Optional

import httpx

from backend.src.core.logging import get_logger

logger = get_logger(__name__)


class DeploymentMonitor:
    """Monitor GitHub Actions deployments and site availability."""

    def __init__(self, github_token: str, username: str):
        """Initialize deployment monitor.

        Args:
            github_token: GitHub personal access token
            username: GitHub username
        """
        self.token = github_token
        self.username = username
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json"
        }

    async def wait_for_workflow_completion(
        self,
        repo_name: str,
        timeout_seconds: int = 600,
        poll_interval: int = 10
    ) -> dict:
        """Wait for the latest GitHub Actions workflow to complete.

        Args:
            repo_name: Repository name
            timeout_seconds: Maximum time to wait (default: 10 minutes)
            poll_interval: Seconds between polls (default: 10)

        Returns:
            Final workflow run data

        Raises:
            TimeoutError: If workflow doesn't complete within timeout
            Exception: If workflow fails
        """
        logger.info(f"Waiting for workflow completion for {repo_name}")

        start_time = asyncio.get_event_loop().time()

        async with httpx.AsyncClient() as client:
            while True:
                # Check timeout
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout_seconds:
                    raise TimeoutError(
                        f"Workflow did not complete within {timeout_seconds} seconds"
                    )

                # Get latest workflow run
                response = await client.get(
                    f"{self.base_url}/repos/{self.username}/{repo_name}/actions/runs?per_page=1",
                    headers=self.headers,
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    runs = data.get("workflow_runs", [])

                    if runs:
                        run = runs[0]
                        status = run["status"]
                        conclusion = run.get("conclusion")

                        logger.info(f"Workflow status: {status}, conclusion: {conclusion}")

                        if status == "completed":
                            if conclusion == "success":
                                logger.info("Workflow completed successfully")
                                return run
                            else:
                                raise Exception(
                                    f"Workflow failed with conclusion: {conclusion}"
                                )

                # Wait before next poll
                await asyncio.sleep(poll_interval)

    async def check_site_availability(
        self,
        site_url: str,
        timeout_seconds: int = 300,
        poll_interval: int = 10
    ) -> bool:
        """Check if the deployed site is accessible.

        Args:
            site_url: URL of the deployed site
            timeout_seconds: Maximum time to wait (default: 5 minutes)
            poll_interval: Seconds between checks (default: 10)

        Returns:
            True if site is accessible

        Raises:
            TimeoutError: If site doesn't become available within timeout
        """
        logger.info(f"Checking site availability: {site_url}")

        start_time = asyncio.get_event_loop().time()

        async with httpx.AsyncClient() as client:
            while True:
                # Check timeout
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout_seconds:
                    raise TimeoutError(
                        f"Site did not become available within {timeout_seconds} seconds"
                    )

                try:
                    response = await client.get(
                        site_url,
                        timeout=10.0,
                        follow_redirects=True
                    )

                    if response.status_code == 200:
                        logger.info(f"Site is live: {site_url}")
                        return True
                    else:
                        logger.debug(f"Site returned {response.status_code}, retrying...")

                except (httpx.ConnectError, httpx.TimeoutException) as e:
                    logger.debug(f"Site not yet accessible: {e}, retrying...")

                # Wait before next check
                await asyncio.sleep(poll_interval)

    async def monitor_deployment(
        self,
        repo_name: str,
        site_url: str,
        workflow_timeout: int = 600,
        site_timeout: int = 300
    ) -> dict:
        """Monitor complete deployment process.

        Args:
            repo_name: Repository name
            site_url: Expected site URL
            workflow_timeout: Timeout for workflow completion (seconds)
            site_timeout: Timeout for site availability (seconds)

        Returns:
            Deployment status dict

        Raises:
            Exception: If deployment fails
        """
        logger.info(f"Monitoring deployment for {repo_name}")

        result = {
            "workflow_completed": False,
            "site_live": False,
            "workflow_data": None
        }

        try:
            # Wait for workflow to complete
            workflow_data = await self.wait_for_workflow_completion(
                repo_name=repo_name,
                timeout_seconds=workflow_timeout
            )
            result["workflow_completed"] = True
            result["workflow_data"] = workflow_data

            # Wait for site to become available
            site_live = await self.check_site_availability(
                site_url=site_url,
                timeout_seconds=site_timeout
            )
            result["site_live"] = site_live

            logger.info(f"Deployment monitoring complete for {repo_name}")
            return result

        except Exception as e:
            logger.error(f"Deployment monitoring failed: {e}")
            raise
