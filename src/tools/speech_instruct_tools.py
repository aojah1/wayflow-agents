# Convert Voice to Text
from wayflowcore.agent import Agent
from wayflowcore.executors.executionstatus import (
    FinishedStatus,
    UserMessageRequestStatus,
)
from wayflowcore.tools import tool

@tool(description_mode="only_docstring")
def voice_to_text_tool(query: str) -> str:
    """Tool that is invoked for a audio .mp3 file detailing the order, and returns the tool name.

    Parameters
    ----------
    query:
        file type

    Returns
    -------
        tool name

    """
    return 'voice_to_text_tool'