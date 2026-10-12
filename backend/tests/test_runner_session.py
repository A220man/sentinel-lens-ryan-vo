"""Unit tests for the programmatic runner engine open_session() and fixture graph."""

import pytest
from app.core.runner import open_session


@pytest.mark.anyio
async def test_open_session_initializes_fixtures():
    session = await open_session(cwd="/test-repo", target="web")
    try:
        assert session.session_id.startswith("sess-")
        assert session.target == "web"
        assert not session.is_closed

        # Verify fixture graph
        assert session.fixtures.device.target == "web"
        assert session.fixtures.device.viewport_width == 1280
        assert session.fixtures.device.viewport_height == 800
        assert session.fixtures.app.is_running
        assert session.fixtures.screen is not None
        assert session.fixtures.agent is not None
        assert session.fixtures.network is not None
    finally:
        await session.close()


@pytest.mark.anyio
async def test_session_agent_act_creates_step_and_artifacts():
    session = await open_session(target="mobile_android")
    try:
        step = await session.fixtures.agent.act("open search and enter query")
        assert step.step_index == 1
        assert step.action == "act"
        assert step.status == "passed"
        assert len(step.artifacts) == 2
        
        art_types = {a["type"] for a in step.artifacts}
        assert "dom_snapshot" in art_types
        assert "screenshot" in art_types

        assert len(session.steps()) == 1
        assert len(session.artifacts()) == 2
    finally:
        await session.close()


@pytest.mark.anyio
async def test_session_agent_assert_visible():
    session = await open_session()
    try:
        # Existing element in default screen fixture
        pass_step = await session.fixtures.agent.assert_visible("Sentinel Lens Dashboard")
        assert pass_step.status == "passed"
        assert pass_step.error is None

        # Non-existing element
        fail_step = await session.fixtures.agent.assert_visible("NonExistentComponent12345")
        assert fail_step.status == "failed"
        assert "not found" in fail_step.error
    finally:
        await session.close()


@pytest.mark.anyio
async def test_session_close_is_idempotent():
    session = await open_session()
    res1 = await session.close()
    assert res1["status"] == "closed"
    assert session.is_closed
    assert not session.fixtures.device.is_active

    # Subsequent close must be idempotent
    res2 = await session.close()
    assert res2["status"] == "already_closed"


@pytest.mark.anyio
async def test_session_async_context_manager():
    async with await open_session(target="mobile_ios") as session:
        step = await session.fixtures.agent.click("#btn-run-suite")
        assert step.action == "click"
        assert step.status == "passed"
    assert session.is_closed
