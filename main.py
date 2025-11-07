import asyncio
import os
from pydantic import BaseModel, Field

from flock import Flock
from flock.mcp import StdioServerParameters
from flock.registry import  flock_type


@flock_type
class Task(BaseModel):
    title: str
    repository: str = Field(..., description="GitHub repository in the format 'owner/repo'")
    content: str = Field(..., description="Detailed description of the task")
    implementation_steps: list[str] = Field(..., description="Step-by-step implementation plan")
    acceptance_criteria: list[str] = Field(..., description="Acceptance criteria for the task", min_items=3)
    test_cases: list[str] = Field(..., description="Test cases to validate the task")


@flock_type
class Issue(BaseModel):
    title: str
    repository: str = Field(..., description="GitHub repository in the format 'owner/repo'")
    content: str = Field(..., description="Detailed description of the issue")
    url: str


@flock_type
class Project(BaseModel):
    title: str
    description: str


flock = Flock("azure/gpt-4.1")

flock.add_mcp(
    name="create_repository_tool",
    enable_tools_feature=True,
    tool_whitelist=["create_repository"],
    connection_params=StdioServerParameters(
        command="docker",
        args=[
            "run",
            "-i",
            "--rm",
            "-e",
            "GITHUB_PERSONAL_ACCESS_TOKEN",
            "ghcr.io/github/github-mcp-server",
        ],
        env={
            "GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", ""),
        },
    ),
)


flock.add_mcp(
    name="github_tools",
    enable_tools_feature=True,
    connection_params=StdioServerParameters(
        command="docker",
        args=[
            "run",
            "-i",
            "--rm",
            "-e",
            "GITHUB_PERSONAL_ACCESS_TOKEN",
            "ghcr.io/github/github-mcp-server",
        ],
        env={
            "GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", ""),
        },
    ),
)


(
    flock.agent("task_generator").description("Generates a list of tasks for a project and creates the repository on GitHub with the create_repository_tool.")
                                .with_mcps(["create_repository_tool"])
                                .consumes(Project)
                                .publishes(Task, fan_out=5)
)


(
    flock.agent("issue_creator").description("Creates a github issue for a given task in the specified repository using the github mcp tools.")
                                .with_mcps(["github_tools"])
                                .consumes(Task)
                                .publishes(Issue)
                                .max_concurrency(5)
)

async def main():
    await flock.serve(dashboard=True)


if __name__ == "__main__":
    asyncio.run(main())