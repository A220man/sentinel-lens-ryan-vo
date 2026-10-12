"""Core programmatic runner session engine for embedding Sentinel Lens in host test suites."""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from app.core.redaction import RedactionFilter, default_redactor


@dataclass
class DeviceLease:
    lease_id: str
    target: str
    viewport_width: int
    viewport_height: int
    user_agent: str
    orientation: str = "portrait"
    is_active: bool = True

    def rotate(self) -> None:
        self.viewport_width, self.viewport_height = self.viewport_height, self.viewport_width
        self.orientation = "landscape" if self.orientation == "portrait" else "portrait"


@dataclass
class ScreenFixture:
    device: DeviceLease
    current_url: str = "http://localhost:3000/app"
    dom_tree: Dict[str, Any] = field(default_factory=lambda: {
        "tag": "div",
        "id": "root",
        "children": [
            {"tag": "header", "role": "banner", "text": "Sentinel Lens Dashboard"},
            {"tag": "main", "role": "main", "children": [
                {"tag": "input", "role": "searchbox", "placeholder": "Search test cases...", "id": "search-input"},
                {"tag": "button", "role": "button", "text": "Run Suite", "id": "btn-run-suite", "aria-label": "Execute E2E suite"},
                {"tag": "div", "role": "status", "id": "status-badge", "text": "Ready"},
            ]},
            {"tag": "footer", "role": "contentinfo", "text": "Test Environment Ready"}
        ]
    })

    def capture_dom(self) -> Dict[str, Any]:
        return dict(self.dom_tree)

    def capture_screenshot_svg(self) -> str:
        w, h = self.device.viewport_width, self.device.viewport_height
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<rect width="100%" height="100%" fill="#0f172a"/>'
            f'<text x="20" y="40" fill="#38bdf8" font-family="sans-serif" font-size="20">Target: {self.device.target}</text>'
            f'<text x="20" y="80" fill="#94a3b8" font-family="sans-serif" font-size="14">Viewport: {w}x{h}</text>'
            f'<rect x="20" y="110" width="{w-40}" height="40" rx="6" fill="#1e293b"/>'
            f'<text x="35" y="135" fill="#f8fafc" font-family="sans-serif" font-size="14">Search test cases...</text>'
            f'<rect x="20" y="170" width="120" height="36" rx="6" fill="#0284c7"/>'
            f'<text x="45" y="193" fill="#ffffff" font-family="sans-serif" font-size="14" font-weight="bold">Run Suite</text>'
            f'</svg>'
        )


@dataclass
class AppFixture:
    app_id: str
    cwd: str
    is_running: bool = True
    process_pid: int = 42100

    def restart(self) -> None:
        self.is_running = True

    def stop(self) -> None:
        self.is_running = False


@dataclass
class NetworkFixture:
    mock_rules: Dict[str, Any] = field(default_factory=dict)
    captured_requests: List[Dict[str, Any]] = field(default_factory=list)

    def mock_route(self, url_pattern: str, response_payload: Dict[str, Any]) -> None:
        self.mock_rules[url_pattern] = response_payload

    def record_request(self, method: str, url: str, status_code: int = 200, latency_ms: float = 18.5) -> None:
        self.captured_requests.append({
            "id": str(uuid.uuid4()),
            "method": method,
            "url": url,
            "status_code": status_code,
            "latency_ms": latency_ms,
            "timestamp": time.time(),
        })


@dataclass
class StepRecord:
    step_id: str
    step_index: int
    action: str
    selector: Optional[str]
    input_payload: Any
    output_payload: Any
    duration_ms: float
    status: str
    error: Optional[str] = None
    artifacts: List[Dict[str, Any]] = field(default_factory=list)


class AgentFixture:
    """Multimodal actor fixture executing autonomous test actions."""

    def __init__(self, session: "RunnerSession"):
        self.session = session

    async def act(self, instruction: str) -> StepRecord:
        """Executes a high-level goal instruction, breaking it into deterministic actions."""
        start_t = time.perf_counter()
        step_id = str(uuid.uuid4())
        
        # Scrub instructions through redaction filter
        clean_instruction = self.session.redactor.redact_text(instruction)
        
        # Deterministic simulation of test step execution
        output: Dict[str, Any] = {
            "instruction": clean_instruction,
            "matched_elements": ["#search-input", "#btn-run-suite"],
            "action_executed": "click_and_verify",
            "screen_state": "updated",
        }
        duration = round((time.perf_counter() - start_t) * 1000 + 12.0, 2)
        
        record = StepRecord(
            step_id=step_id,
            step_index=len(self.session.step_history) + 1,
            action="act",
            selector=None,
            input_payload={"instruction": clean_instruction},
            output_payload=output,
            duration_ms=duration,
            status="passed",
        )
        return await self.session.record_step(record)

    async def assert_visible(self, selector_or_text: str) -> StepRecord:
        start_t = time.perf_counter()
        step_id = str(uuid.uuid4())
        clean_target = self.session.redactor.redact_text(selector_or_text)
        
        # Verify against DOM tree
        dom = self.session.fixtures.screen.capture_dom()
        found = False
        def search_node(node: Dict[str, Any]) -> bool:
            if clean_target.lower() in str(node.get("text", "")).lower() or clean_target == node.get("id"):
                return True
            for ch in node.get("children", []):
                if search_node(ch):
                    return True
            return False

        found = search_node(dom)
        duration = round((time.perf_counter() - start_t) * 1000 + 4.5, 2)
        
        record = StepRecord(
            step_id=step_id,
            step_index=len(self.session.step_history) + 1,
            action="assert_visible",
            selector=clean_target,
            input_payload={"target": clean_target},
            output_payload={"verified": found, "match_type": "accessibility_text"},
            duration_ms=duration,
            status="passed" if found else "failed",
            error=None if found else f"Element '{clean_target}' not found in current DOM state",
        )
        return await self.session.record_step(record)

    async def click(self, selector: str) -> StepRecord:
        start_t = time.perf_counter()
        step_id = str(uuid.uuid4())
        clean_selector = self.session.redactor.redact_text(selector)
        duration = round((time.perf_counter() - start_t) * 1000 + 8.2, 2)

        record = StepRecord(
            step_id=step_id,
            step_index=len(self.session.step_history) + 1,
            action="click",
            selector=clean_selector,
            input_payload={"selector": clean_selector},
            output_payload={"event": "pointerdown->pointerup->click", "coordinates": [45, 185]},
            duration_ms=duration,
            status="passed",
        )
        return await self.session.record_step(record)


@dataclass
class FixtureGraph:
    device: DeviceLease
    screen: ScreenFixture
    app: AppFixture
    network: NetworkFixture
    agent: Optional[AgentFixture] = None


class RunnerSession:
    """The programmatic test session created by open_session()."""

    def __init__(
        self,
        session_id: str,
        cwd: str,
        target: str,
        config: Dict[str, Any],
        on_step: Optional[Callable[[StepRecord], None]] = None,
        redactor: Optional[RedactionFilter] = None,
    ):
        self.session_id = session_id
        self.cwd = cwd
        self.target = target
        self.config = config
        self.on_step = on_step
        self.redactor = redactor or default_redactor
        self.is_closed = False
        self.step_history: List[StepRecord] = []
        self.artifacts_list: List[Dict[str, Any]] = []

        # Target dimensions
        viewport_map = {
            "web": (1280, 800),
            "mobile_android": (412, 915),
            "mobile_ios": (393, 852),
            "desktop": (1920, 1080),
        }
        vw, vh = viewport_map.get(target, (1280, 800))

        device = DeviceLease(
            lease_id=f"device-{uuid.uuid4().hex[:8]}",
            target=target,
            viewport_width=vw,
            viewport_height=vh,
            user_agent=f"SentinelLensRunner/1.0 ({target})",
        )
        screen = ScreenFixture(device=device)
        app = AppFixture(app_id=f"app-{uuid.uuid4().hex[:8]}", cwd=cwd)
        network = NetworkFixture()

        self.fixtures = FixtureGraph(
            device=device,
            screen=screen,
            app=app,
            network=network,
        )
        self.fixtures.agent = AgentFixture(self)

    async def record_step(self, step: StepRecord) -> StepRecord:
        """Sanitizes step payload through redaction filter, creates artifacts, and notifies on_step."""
        step.input_payload = self.redactor.redact_data(step.input_payload)
        step.output_payload = self.redactor.redact_data(step.output_payload)

        # Generate step artifacts: DOM snapshot and screenshot
        dom_snapshot = self.fixtures.screen.capture_dom()
        screenshot_svg = self.fixtures.screen.capture_screenshot_svg()
        
        dom_artifact = {
            "artifact_id": str(uuid.uuid4()),
            "step_id": step.step_id,
            "type": "dom_snapshot",
            "mime_type": "application/json",
            "content": self.redactor.redact_data(dom_snapshot),
        }
        screen_artifact = {
            "artifact_id": str(uuid.uuid4()),
            "step_id": step.step_id,
            "type": "screenshot",
            "mime_type": "image/svg+xml",
            "content": screenshot_svg,
        }
        step.artifacts = [dom_artifact, screen_artifact]
        self.artifacts_list.extend(step.artifacts)

        self.step_history.append(step)

        if self.on_step:
            try:
                if asyncio.iscoroutinefunction(self.on_step):
                    await self.on_step(step)
                else:
                    self.on_step(step)
            except Exception:
                pass  # Host reporting errors must not abort runner session

        return step

    def steps(self) -> List[StepRecord]:
        return list(self.step_history)

    def artifacts(self) -> List[Dict[str, Any]]:
        return list(self.artifacts_list)

    async def close(self) -> Dict[str, Any]:
        """Idempotent cleanup releasing device leases and child processes."""
        if self.is_closed:
            return {"status": "already_closed", "session_id": self.session_id}

        self.is_closed = True
        self.fixtures.device.is_active = False
        self.fixtures.app.stop()

        cleanup_report = {
            "session_id": self.session_id,
            "target": self.target,
            "steps_executed": len(self.step_history),
            "artifacts_collected": len(self.artifacts_list),
            "device_released": self.fixtures.device.lease_id,
            "cleanup_errors": [],
            "status": "closed",
        }
        return cleanup_report

    async def __aenter__(self) -> "RunnerSession":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()


async def open_session(
    cwd: str = "/repo",
    config: Optional[Dict[str, Any]] = None,
    target: str = "web",
    on_step: Optional[Callable[[StepRecord], None]] = None,
    redactor: Optional[RedactionFilter] = None,
) -> RunnerSession:
    """Entry point function exposing openSession() on sentinel_lens.runner for host test runners."""
    session_id = f"sess-{uuid.uuid4().hex[:12]}"
    session = RunnerSession(
        session_id=session_id,
        cwd=cwd,
        target=target,
        config=config or {},
        on_step=on_step,
        redactor=redactor,
    )
    return session
