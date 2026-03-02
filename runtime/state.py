from typing import TypedDict, Annotated
from operator import add


class ConversationState(TypedDict):
    """State that flows through the LangGraph dialog execution.

    messages  – full conversation log (appended by each node via the `add` reducer)
    variables – extracted entity values (replaced wholesale by each node that updates it)
    """

    messages: Annotated[list[dict], add]
    variables: dict
