from github import Github
from mcp.server.fastmcp import FastMCP

from app.config.settings import GITHUB_TOKEN


mcp = FastMCP("GitHub MCP Server")


def get_github_client():
    """Create an authenticated GitHub client."""

    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN is missing from .env")

    return Github(
        login_or_token=GITHUB_TOKEN,
        timeout=15,
        per_page=10,
    )


@mcp.tool()
def get_github_user(username: str) -> dict:
    """Get information about a GitHub user."""

    github = get_github_client()
    user = github.get_user(username)

    return {
        "username": user.login,
        "name": user.name,
        "bio": user.bio,
        "public_repositories": user.public_repos,
        "followers": user.followers,
        "following": user.following,
        "location": user.location,
        "company": user.company,
        "profile_url": user.html_url,
    }


@mcp.tool()
def get_repository_info(repo_name: str) -> dict:
    """Get basic information about a GitHub repository."""

    github = get_github_client()
    repo = github.get_repo(repo_name)

    return {
        "name": repo.full_name,
        "description": repo.description,
        "stars": repo.stargazers_count,
        "forks": repo.forks_count,
        "open_issues": repo.open_issues_count,
        "language": repo.language,
        "url": repo.html_url,
    }


@mcp.tool()
def list_repository_issues(
    repo_name: str,
    state: str = "open",
) -> list[dict]:
    """List up to 10 issues from a GitHub repository."""

    github = get_github_client()
    repo = github.get_repo(repo_name)

    issues = repo.get_issues(
        state=state,
        sort="updated",
        direction="desc",
    )

    results = []

    for issue in issues[:10]:
        results.append(
            {
                "number": issue.number,
                "title": issue.title,
                "state": issue.state,
                "url": issue.html_url,
            }
        )

    return results


@mcp.tool()
def get_repository_readme(repo_name: str) -> str:
    """Get the README content of a GitHub repository."""

    github = get_github_client()
    repo = github.get_repo(repo_name)

    readme = repo.get_readme()

    return readme.decoded_content.decode("utf-8")


if __name__ == "__main__":
    mcp.run()