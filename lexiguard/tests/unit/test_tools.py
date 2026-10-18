
import pytest

from app.agent.tools import ToolContext, ToolName, ToolRejected, validate_next_action
from app.schemas.model_io import NextAction


def context() -> ToolContext:
    return ToolContext(document_id="d1", page_count=10, known_refs=frozenset({"ev_0001"}))


def test_page_must_be_inside_document():
    with pytest.raises(ToolRejected):
        validate_next_action(NextAction(action="GET_PAGE", page=99), context())


def test_ref_must_have_been_returned_earlier():
    with pytest.raises(ToolRejected):
        validate_next_action(NextAction(action="FIND_RELATED", ref="ev_9999"), context())


def test_model_selectable_tools_only():
    tool = validate_next_action(NextAction(action="SEARCH", query="notice"), context())
    assert tool is ToolName.SEARCH_DOCUMENT


def test_answer_is_not_a_tool_call():
    with pytest.raises(ToolRejected):
        validate_next_action(NextAction(action="ANSWER"), context())


def test_evidence_tool_is_not_model_selectable_by_construction():
    assert "get_evidence" not in {tool.value for tool in ToolName if tool.value.startswith("search")}
