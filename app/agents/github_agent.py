import json

from langchain_groq import ChatGroq

from app.config.settings import GROQ_API_KEY, MODEL_NAME
from app.mcp.github_client import call_github_tool_sync


llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=MODEL_NAME,
    temperature=0,
)


def ask_github_agent(question: str) -> str:
    """
    GitHub specialist agent using a real MCP client.

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

            result = call_github_tool_sync(
                "get_github_user",
                {
                    "username": username,
                },
            )

            user = extract_mcp_json(result)

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

            result = call_github_tool_sync(
                "get_repository_readme",
                {
                    "repo_name": repo_name,
                },
            )

            readme = extract_mcp_text(result)

            if not readme:
                return "No readable README was found."

            return readme[:6000]

        # ==========================================
        # ISSUES
        # ==========================================

        if "issue" in question_lower:

            result = call_github_tool_sync(
                "list_repository_issues",
                {
                    "repo_name": repo_name,
                },
            )

            issues = extract_mcp_json(result)

            if not issues:
                return f"There are no open issues in {repo_name}."

            output = [
                f"Open issues in {repo_name}:"
            ]

            for issue in issues:
                output.append(
                    f"\n#{issue['number']} - {issue['title']}\n"
                    f"State: {issue['state']}\n"
                    f"URL: {issue['url']}"
                )

            return "\n".join(output)

        # ==========================================
        # REPOSITORY INFORMATION
        # ==========================================

        result = call_github_tool_sync(
            "get_repository_info",
            {
                "repo_name": repo_name,
            },
        )

        info = extract_mcp_json(result)

        return format_repository_info(info)

    except Exception as error:

        return (
            "GitHub Agent Error:\n"
            f"{error}"
        )


# ==================================================
# MCP RESULT HELPERS
# ==================================================


def extract_mcp_json(result):
    """
    Extract JSON data returned by an MCP tool.
    """

    if getattr(result, "isError", False):
        raise RuntimeError(
            "GitHub MCP tool returned an error."
        )

    if not result.content:
        raise RuntimeError(
            "GitHub MCP tool returned no content."
        )

    text = result.content[0].text

    return json.loads(text)


def extract_mcp_text(result):
    """
    Extract plain text returned by an MCP tool.
    """

    if getattr(result, "isError", False):
        raise RuntimeError(
            "GitHub MCP tool returned an error."
        )

    if not result.content:
        return ""

    return result.content[0].text


# ==================================================
# REPOSITORY NAME EXTRACTION
# ==================================================


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


# ==================================================
# USERNAME EXTRACTION
# ==================================================


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


# ==================================================
# FORMAT USER INFORMATION
# ==================================================


def format_user_info(user: dict) -> str:

    return (
        f"GitHub Username: "
        f"{user.get('username', 'Unknown')}\n"
        f"Name: "
        f"{user.get('name') or 'Not provided'}\n"
        f"Bio: "
        f"{user.get('bio') or 'No bio'}\n"
        f"Public Repositories: "
        f"{user.get('public_repositories', 0)}\n"
        f"Followers: "
        f"{user.get('followers', 0)}\n"
        f"Following: "
        f"{user.get('following', 0)}\n"
        f"Location: "
        f"{user.get('location') or 'Not provided'}\n"
        f"Company: "
        f"{user.get('company') or 'Not provided'}\n"
        f"Profile: "
        f"{user.get('profile_url', 'Not available')}"
    )


# ==================================================
# FORMAT REPOSITORY INFORMATION
# ==================================================


def format_repository_info(info: dict) -> str:

    return (
        f"Repository: "
        f"{info.get('name', 'Unknown')}\n"
        f"Description: "
        f"{info.get('description') or 'No description'}\n"
        f"Stars: "
        f"{info.get('stars', 0)}\n"
        f"Forks: "
        f"{info.get('forks', 0)}\n"
        f"Open Issues: "
        f"{info.get('open_issues', 0)}\n"
        f"Language: "
        f"{info.get('language') or 'Not specified'}\n"
        f"URL: "
        f"{info.get('url', 'Not available')}"
    )