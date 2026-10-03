import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


BASE_DIR = Path(__file__).resolve().parents[2]


async def call_calendar_tool(
    tool_name: str,
    arguments: dict,
):
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[
            "-m",
            "app.mcp.calendar_server",
        ],
        cwd=str(BASE_DIR),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:

            await session.initialize()

            result = await session.call_tool(
                tool_name,
                arguments,
            )

            return result


def call_calendar_tool_sync(
    tool_name: str,
    arguments: dict,
):
    return asyncio.run(
        call_calendar_tool(
            tool_name,
            arguments,
        )
    )