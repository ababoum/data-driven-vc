import datetime
import logging

from providers.github import GitHubClient
from providers.predictleads.client import PredictleadsClient

logger = logging.getLogger(__name__)


class GitHubAnalyzer:
    repo: str = None
    owner: str = None
    _repo_data: dict = None
    _color: int = None
    _report: str = None

    def __init__(self, domain: str):
        self.domain = domain
        self.client = GitHubClient()

    @property
    def color(self) -> int:
        return self._color

    @property
    def report(self) -> str:
        return self._report

    @property
    def repo_data(self) -> dict | None:
        return self._repo_data

    async def find_github(self):
        logger.info('Finding GitHub repo...')
        repo_full_name = await PredictleadsClient().fetch_github(self.domain)
        if repo_full_name:
            self.owner, self.repo = repo_full_name.split('/')
            logger.info(f'Found GitHub repo: {repo_full_name}')
            return True
        else:
            logger.info('No GitHub repo found')
            return False

    async def get_repo_data(self):
        if self._repo_data is None:
            self._repo_data = await self.client.get_repo(self.owner, self.repo)
        return self._repo_data

    async def get_stars_growth_rate(self) -> int:
        repo_data = await self.get_repo_data()
        created_at = datetime.datetime.strptime(repo_data['created_at'], "%Y-%m-%dT%H:%M:%SZ")
        stars = repo_data['stargazers_count']
        months_since_creation = max((datetime.datetime.now() - created_at).days / 30, 1)
        rate = stars / months_since_creation
        rate = int(min(10, max(1, rate / 100)))  # Normalize to a scale of 1 to 10
        logger.info(f"Stars growth rate: {rate}")
        return rate

    async def get_forks_rate(self) -> int:
        repo_data = await self.get_repo_data()
        forks = repo_data['forks_count']
        rate = int(min(10, max(1, forks / 100)))  # Normalize to a scale of 1 to 10
        logger.info(f"Forks count: {rate}")
        return rate

    async def get_commit_frequency_rate(self) -> int:
        repo_data = await self.get_repo_data()
        commit_count = repo_data['commits_count']
        created_at = datetime.datetime.strptime(repo_data['created_at'], "%Y-%m-%dT%H:%M:%SZ")
        months_since_creation = max((datetime.datetime.now() - created_at).days / 30, 1)
        rate = commit_count / months_since_creation
        rate = int(min(10, max(1, rate / 20)))  # Normalize to a scale of 1 to 10
        logger.info(f"Commit frequency: {rate}")
        return rate

    async def get_contributors_rate(self) -> int:
        contributors = await self.client.get_contributors(self.owner, self.repo)
        count = len(contributors)
        rate = int(min(10.0, max(1.0, count / 10)))  # Normalize to a scale of 1 to 10
        logger.info(f"Contributors rate: {rate}")
        return rate

    async def get_issue_resolution_rate(self) -> int:
        issues = await self.client.get_issues(self.owner, self.repo)
        resolution_times = []
        for issue in issues:
            if issue.get('state') == 'closed' and 'closed_at' in issue:
                created_at = datetime.datetime.strptime(issue['created_at'], "%Y-%m-%dT%H:%M:%SZ")
                closed_at = datetime.datetime.strptime(issue['closed_at'], "%Y-%m-%dT%H:%M:%SZ")
                resolution_times.append((closed_at - created_at).total_seconds() / 3600 / 24)
        avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else float('inf')
        if avg_resolution_time == float('inf'):
            return 1
        logger.info(f"Average issue resolution time: {avg_resolution_time:.1f} days")
        rate = int(min(10.0, max(1.0, 30 / avg_resolution_time)))  # Normalize to a scale of 1 to 10
        logger.info(f"Issue resolution rate: {rate}")
        return rate

    async def run_analysis(self):
        success = await self.find_github()
        if not success:
            self._color = -1
            self._report = "No GitHub repository found."
            return

        stars_rate = await self.get_stars_growth_rate()
        forks_rate = await self.get_forks_rate()
        commit_rate = await self.get_commit_frequency_rate()
        contributors_rate = await self.get_contributors_rate()
        issue_resolution_rate = await self.get_issue_resolution_rate()
        # sum all rates
        total_rate = stars_rate + forks_rate + commit_rate + contributors_rate + issue_resolution_rate
        if total_rate < 10:
            self._color = -1
        elif total_rate < 25:
            self._color = 0
        else:
            self._color = 1

        report = f"""
# GitHub Repository Analysis Report: {self.owner}/{self.repo}

## Metrics

- **Stars Growth Rate:** {stars_rate}/10
- **Forks Rate:** {forks_rate}/10
- **Commit Frequency Rate:** {commit_rate}/10
- **Contributors Rate:** {contributors_rate}/10
- **Issue Resolution Rate:** {issue_resolution_rate}/10
"""
        self._report = report


async def main():
    from dotenv import load_dotenv
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    analyzer = GitHubAnalyzer("facebook/react")
    await analyzer.run_analysis()
    print(analyzer.report)


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
