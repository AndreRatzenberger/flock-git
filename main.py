import asyncio
import os
from pydantic import BaseModel, Field

from flock import Flock
from flock.mcp import StdioServerParameters
from flock.registry import  flock_type


@flock_type
class Task(BaseModel):
    title: str
    content: str = Field(..., description="Detailed description of the task")
    acceptance_criteria: list[str] = Field(..., description="Acceptance criteria for the task", min_items=3)
    url: str


@flock_type
class TaskList(BaseModel):
    tasks: list[Task]


@flock_type
class Project(BaseModel):
    title: str
    description: str


flock = Flock("azure/gpt-4.1")

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
    flock.agent("task_generator").description("Generates a list of tasks for a project and creates with the github mcp tools" 
                                          "a new github project with an issue for each task.")
                                .with_mcps(["github_tools"])
                                .consumes(Project)
                                .publishes(TaskList)
)

async def main():
    await flock.serve(dashboard=True)


if __name__ == "__main__":
    asyncio.run(main())