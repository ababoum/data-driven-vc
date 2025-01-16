import os
from pathlib import Path
from string import Template
import httpx

from providers.github.utils import extract_nested_fields


class GitHubClient:
    base_url = 'https://api.github.com/graphql'

    def __init__(self, token: str = None):
        token = token or os.getenv('GITHUB_TOKEN')
        self.headers = {
            "Authorization": f"token {token}"
        }

    def get_query_from_file(self, filename: str) -> str:
        with open(Path(__file__).resolve().parent / 'queries' / filename, 'r') as f:
            return f.read()

    async def run_query(self, query: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                json={'query': query},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    def _serialize_repo(raw_item: dict) -> dict:
        mapper: dict[str, str] = {
            "archived": "isArchived",
            "created_at": "createdAt",
            "default_branch": "defaultBranchRef.name",
            "description": "description",
            "fork": "isFork",
            "forks_count": "forkCount",
            "full_name": "nameWithOwner",
            "has_issues": "hasIssuesEnabled",
            "has_projects": "hasProjectsEnabled",
            "has_wiki": "hasWikiEnabled",
            "has_downloads": "latestRelease.id",
            "homepage": "homepageUrl",
            "language": "languages.edges.node.name",
            "license_name": "licenseInfo.name",
            "owner_node_id": "owner.id",
            "owner_id": "owner.databaseId",
            "owner_login": "owner.login",
            "owner_type": "owner.__typename",
            "pushed_at": "pushedAt",
            "repo_id": "databaseId",
            "mentionable_users": "mentionableUsers.totalCount",
            "size": "diskUsage",
            "stargazers_count": "stargazerCount",
            "commits_count": "defaultBranchRef.target.history.totalCount",
            "topics": "repositoryTopics.edges.node.topic.name",
            "updated_at": "updatedAt",
            "watchers_count": "watchers.totalCount",
            "latest_commit_date": "defaultBranchRef.target.history.edges.node.committedDate",
            "open_issues_count": "openIssues.totalCount",
            "closed_issues_count": "closedIssues.totalCount",
            "open_pull_requests_count": "openPullRequests.totalCount",
            "closed_pull_requests_count": "closedPullRequests.totalCount",
            "merged_pull_requests_count": "mergedPullRequests.totalCount",
            "tags_count": "tags.totalCount"
        }
        # Main mapping
        item = extract_nested_fields(raw_item, mapper)
        # Topics: list to str
        topics = raw_item['repositoryTopics']['edges']
        if topics:
            item['topics'] = '|'.join([x['node']['topic']['name'] for x in topics])
        else:
            item['topics'] = None
        item['has_downloads'] = (item['has_downloads'] is not None) or (item['tags_count'] > 0)
        del item['tags_count']
        item['has_pages'] = item['homepage'] is not None

        readme_keys = ['readme1', 'readme2', 'readme3']
        for key in readme_keys:
            if raw_item.get(key):
                item['readme'] = raw_item[key]['text']
                break
        return item

    @staticmethod
    def _serialize_user(raw_item: dict):
        mapper = {
            "user_id": 'databaseId',
            "login": 'login',
            "type": '__typename',
            "name": 'name',
            "company": 'company',
            'blog': 'websiteUrl',
            "location": 'location',
            "email": 'email',
            "hireable": 'isHireable',
            "bio": 'bio',
            "twitter_username": 'twitterUsername',
            "public_repos": 'repositories.totalCount',
            "public_gists": 'gists.totalCount',
            'followers': 'followers.totalCount',
            "following": 'following.totalCount',
            "created_at": 'createdAt',
            "updated_at": 'updatedAt',
            "is_verified": "isVerified"
        }
        return extract_nested_fields(raw_item, mapper)

    async def get_repo(self, owner: str, name: str):
        query = Template(self.get_query_from_file("repo_by_name.graphql")).substitute(
            owner=owner,
            name=name
        )
        data = await self.run_query(query)
        return self._serialize_repo(data['data']['repository'])

    async def get_user(self, username: str) -> dict:
        query = Template(self.get_query_from_file("user_by_name.graphql")).substitute(
            login=username
        )
        data = await self.run_query(query)
        return self._serialize_user(data['data']['repositoryOwner'])

    async def get_contributors(self, owner: str, repo: str) -> dict:
        url = f"https://api.github.com/repos/{owner}/{repo}/contributors"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def get_issues(self, owner: str, repo: str) -> list[dict]:
        url = f"https://api.github.com/repos/{owner}/{repo}/issues?state=all"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def get_commits(self, owner: str, repo: str) -> list[dict]:
        url = f"https://api.github.com/repos/{owner}/{repo}/commits"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
