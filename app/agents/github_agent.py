from langchain_groq import ChatGroq

from app.config.settings import GROQ_API_KEY, MODEL_NAME
from app.mcp.github_server import (
    get_github_user,
    get_repository_info,
    list_repository_issues,
    get_repository_readme,
)


llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=MODEL_NAME,
    temperature=0,
)


def ask_github_agent(question: str) -> str:
    """
    GitHub specialist agent.

    Supports:
    - GitHub user/account information
    - Repository information
    - Repository issues
    - Repository README
    """

    question_lower = question.lower()

    try:

        # ==========================================
        # GITHUB ACCOUNT / USER
        # ==========================================

        if any(
            keyword in question_lower
            for keyword in [
                "github account",
                "github user",
                "github profile",
                "github username",
            ]
        ):

            username = extract_username(question)

            if not username:
                return (
                    "Please provide a GitHub username.\n\n"
                    "Example:\n"
                    "Tell me about the GitHub account microsoft"
                )

            user = get_github_user(username)

            return format_user_info(user)

        # ==========================================
        # FIND REPOSITORY
        # ==========================================

        repo_name = extract_repo_name(question)

        if not repo_name:
            return (
                "Please provide a GitHub repository in this format:\n\n"
                "owner/repository\n\n"
                "Example:\n"
                "microsoft/vscode"
            )

        # ==========================================
        # README
        # ==========================================

        if "readme" in question_lower:

            readme = get_repository_readme(repo_name)

            if not readme:
                return "No readable README was found."

            return readme[:6000]

        # ==========================================
        # ISSUES
        # ==========================================

        if "issue" in question_lower:

            issues = list_repository_issues(repo_name)

            if not issues:
                return (
                    f"There are no open issues in {repo_name}."
                )

            result = [
                f"Open issues in {repo_name}:"
            ]

            for issue in issues:

                result.append(
                    f"\n#{issue['number']} - {issue['title']}\n"
                    f"State: {issue['state']}\n"
                    f"URL: {issue['url']}"
                )

            return "\n".join(result)

        # ==========================================
        # REPOSITORY INFORMATION
        # ==========================================

        info = get_repository_info(repo_name)

        return format_repository_info(info)

    except Exception as error:

        return (
            "GitHub Agent Error:\n"
            f"{error}"
        )


def extract_repo_name(question: str) -> str | None:
    """
    Extract owner/repository from the question.

    Example:
    Tell me about microsoft/vscode

    Returns:
    microsoft/vscode
    """

    words = question.split()

    for word in words:

        cleaned = word.strip(
            " \t\n\r()[]{}<>.,!?\"'`"
        )

        if "/" not in cleaned:
            continue

        parts = cleaned.split("/")

        if len(parts) != 2:
            continue

        owner = parts[0].strip()
        repository = parts[1].strip()

        if owner and repository:

            return f"{owner}/{repository}"

    return None


def extract_username(question: str) -> str | None:
    """
    Extract a GitHub username from the question.

    Example:
    Tell me about the GitHub account microsoft

    Returns:
    microsoft
    """

    words = question.split()

    ignored_words = {
        "tell",
        "me",
        "about",
        "the",
        "github",
        "account",
        "user",
        "profile",
        "username",
        "information",
        "show",
        "give",
        "details",
        "please",
        "what",
        "is",
    }

    for word in words:

        cleaned = word.strip(
            " \t\n\r()[]{}<>.,!?\"'`"
        )

        if cleaned.startswith("@"):
            cleaned = cleaned[1:]

        if not cleaned:
            continue

        if cleaned.lower() in ignored_words:
            continue

        if "/" in cleaned:
            continue

        return cleaned

    return None


def format_user_info(user: dict) -> str:
    """Format GitHub user information."""

    return (
        f"GitHub Username: {user['username']}\n"
        f"Name: {user['name'] or 'Not provided'}\n"
        f"Bio: {user['bio'] or 'No bio'}\n"
        f"Public Repositories: "
        f"{user['public_repositories']}\n"
        f"Followers: {user['followers']}\n"
        f"Following: {user['following']}\n"
        f"Location: "
        f"{user['location'] or 'Not provided'}\n"
        f"Company: "
        f"{user['company'] or 'Not provided'}\n"
        f"Profile: {user['profile_url']}"
    )


def format_repository_info(info: dict) -> str:
    """Format GitHub repository information."""

    return (
        f"Repository: {info['name']}\n"
        f"Description: "
        f"{info['description'] or 'No description'}\n"
        f"Stars: {info['stars']}\n"
        f"Forks: {info['forks']}\n"
        f"Open Issues: {info['open_issues']}\n"
        f"Language: "
        f"{info['language'] or 'Not specified'}\n"
        f"URL: {info['url']}"
    )