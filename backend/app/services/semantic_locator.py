"""Deterministic semantic locator engine for grounding UI test targets in accessibility trees."""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ElementCandidate:
    node_id: str
    tag: str
    role: Optional[str]
    name: Optional[str]
    placeholder: Optional[str]
    test_id: Optional[str]
    text: Optional[str]
    score: float = 0.0
    matched_strategy: str = "none"


class SemanticLocatorEngine:
    """Offline deterministic engine ranking DOM/accessibility nodes for autonomous test actions."""

    ROLE_WEIGHTS: Dict[str, float] = {
        "button": 1.2,
        "searchbox": 1.15,
        "textbox": 1.1,
        "link": 1.0,
        "checkbox": 1.05,
        "combobox": 1.1,
        "menuitem": 1.0,
        "tab": 1.0,
    }

    def flatten_tree(self, root: Dict[str, Any], path: str = "") -> List[ElementCandidate]:
        """Flattens a hierarchical DOM/accessibility snapshot into candidate elements."""
        candidates: List[ElementCandidate] = []
        node_id = str(root.get("id") or path or "node-root")
        cand = ElementCandidate(
            node_id=node_id,
            tag=str(root.get("tag", "div")),
            role=root.get("role"),
            name=root.get("aria-label") or root.get("name"),
            placeholder=root.get("placeholder"),
            test_id=root.get("data-testid") or root.get("testId"),
            text=str(root.get("text", "")).strip() or None,
        )
        candidates.append(cand)

        children = root.get("children", [])
        for idx, child in enumerate(children):
            if isinstance(child, dict):
                candidates.extend(self.flatten_tree(child, path=f"{node_id}/{idx}"))

        return candidates

    def calculate_score(self, target: str, cand: ElementCandidate) -> Tuple[float, str]:
        """Calculates deterministic match confidence score between test target and candidate."""
        clean_target = target.strip().lower()

        # 1. Exact Test ID match
        if cand.test_id and cand.test_id.lower() == clean_target:
            return 1.0, "exact_testid"

        # 2. Exact element ID match
        if cand.node_id.lower() == clean_target.lstrip("#"):
            return 0.98, "exact_element_id"

        # 3. Accessible name match with role weighting
        if cand.name:
            cand_name = cand.name.lower()
            if cand_name == clean_target:
                weight = self.ROLE_WEIGHTS.get(cand.role or "", 1.0)
                return min(0.95 * weight, 0.99), "accessible_name_exact"
            if clean_target in cand_name:
                return 0.82, "accessible_name_contains"

        # 4. Placeholder match (interactive input)
        if cand.placeholder:
            cand_ph = cand.placeholder.lower()
            if cand_ph.startswith(clean_target) or clean_target in cand_ph:
                weight = self.ROLE_WEIGHTS.get(cand.role or "", 1.0)
                return min(0.88 * weight, 0.96), "placeholder_match"

        # 5. Text content match
        if cand.text:
            cand_text = cand.text.lower()
            if cand_text == clean_target:
                # If candidate is a static label and not interactive, slight discount
                discount = 0.90 if cand.tag == "label" else 1.0
                return 0.90 * discount, "text_exact"
            if clean_target in cand_text or cand_text in clean_target:
                return 0.72, "text_contains"

        # 6. Associated label heuristic for form inputs
        if cand.tag == "input" and cand.placeholder and clean_target in cand.placeholder.lower():
            return 0.85, "input_placeholder_associated"

        # 6. Role-based fallback
        if cand.role and cand.role.lower() == clean_target:
            return 0.55, "role_match"

        return 0.0, "none"

    def resolve_target(
        self,
        target_description: str,
        dom_tree: Dict[str, Any],
    ) -> Tuple[Optional[ElementCandidate], bool, List[ElementCandidate]]:
        """Finds the best matching DOM element; returns (best_candidate, is_ambiguous, all_candidates)."""
        candidates = self.flatten_tree(dom_tree)
        scored: List[ElementCandidate] = []

        for cand in candidates:
            score, strategy = self.calculate_score(target_description, cand)
            if score > 0.3:
                cand.score = score
                cand.matched_strategy = strategy
                scored.append(cand)

        scored.sort(key=lambda c: c.score, reverse=True)

        if not scored:
            return None, False, []

        best = scored[0]
        # Ambiguity check: if 2nd candidate is within 0.08 score difference
        is_ambiguous = False
        if len(scored) > 1 and (scored[0].score - scored[1].score) < 0.08:
            is_ambiguous = True

        return best, is_ambiguous, scored


semantic_locator_engine = SemanticLocatorEngine()
