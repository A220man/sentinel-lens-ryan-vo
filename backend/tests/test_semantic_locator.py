"""Tests for deterministic semantic locator resolution and ambiguity scoring."""

from app.services.semantic_locator import SemanticLocatorEngine


def test_semantic_locator_resolves_testid():
    engine = SemanticLocatorEngine()
    dom = {
        "tag": "div",
        "children": [
            {"tag": "button", "data-testid": "submit-order", "text": "Pay Now"},
            {"tag": "p", "text": "Submit order when ready"},
        ],
    }

    best, is_ambiguous, candidates = engine.resolve_target("submit-order", dom)
    assert best is not None
    assert best.test_id == "submit-order"
    assert best.score == 1.0
    assert best.matched_strategy == "exact_testid"
    assert not is_ambiguous


def test_semantic_locator_accessible_name_with_role():
    engine = SemanticLocatorEngine()
    dom = {
        "tag": "nav",
        "children": [
            {"tag": "button", "role": "button", "aria-label": "Close Modal", "id": "btn-close"},
            {"tag": "span", "text": "Close modal note"},
        ],
    }

    best, is_ambiguous, candidates = engine.resolve_target("Close Modal", dom)
    assert best is not None
    assert best.node_id == "btn-close"
    assert best.score > 0.9
    assert best.matched_strategy == "accessible_name_exact"


def test_semantic_locator_detects_ambiguity():
    engine = SemanticLocatorEngine()
    # Two identical buttons with same text
    dom = {
        "tag": "div",
        "children": [
            {"tag": "button", "id": "btn-top-save", "role": "button", "text": "Save Draft"},
            {"tag": "button", "id": "btn-bottom-save", "role": "button", "text": "Save Draft"},
        ],
    }

    best, is_ambiguous, candidates = engine.resolve_target("Save Draft", dom)
    assert best is not None
    assert is_ambiguous is True
    assert len(candidates) >= 2


def test_semantic_locator_returns_none_for_missing():
    engine = SemanticLocatorEngine()
    dom = {
        "tag": "div",
        "children": [{"tag": "p", "text": "Hello world"}],
    }

    best, is_ambiguous, candidates = engine.resolve_target("NonExistentButtonXYZ", dom)
    assert best is None
    assert is_ambiguous is False
    assert len(candidates) == 0
