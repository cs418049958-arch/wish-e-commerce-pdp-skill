#!/usr/bin/env python3
"""Validate blocking planning contracts for ecommerce PDP screens."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


REQUIRED_PROJECT_FIELDS = {"project", "page_type", "style_dna_id", "screens"}
REQUIRED_SCREEN_FIELDS = {
    "screen_id",
    "source_page_or_region",
    "semantic_goal",
    "exact_copy",
    "creative_mechanism",
    "scene_layout",
    "hero_action",
    "entity_count_exact",
    "connection_graph",
    "anchor_positions",
    "shared_axes",
    "entry_exit_ports",
    "primary_secondary_order",
    "evidence_presentation",
    "protected_assets",
    "forbidden_entities",
    "forbidden_substitutions",
    "style_dna_id",
    "status",
}
ALLOWED_PAGE_TYPES = {"long", "short-grayboard"}
ALLOWED_INITIAL_STATUSES = {
    "parsed",
    "contract_validated",
    "style_locked",
    "generated",
    "structure_passed",
    "visual_passed",
    "content_passed",
    "user_approved",
    "final",
}
REQUIRED_CONNECTION_FIELDS = {"from", "to", "relation"}
REQUIRED_ANCHOR_FIELDS = {"entity", "x", "y", "region"}
REQUIRED_PORT_FIELDS = {
    "continuity_group",
    "object",
    "from_screen",
    "to_screen",
    "edge_from",
    "edge_to",
    "normalized_x",
    "diameter_or_width_ratio",
    "material",
    "lighting",
    "direction",
    "occlusion_forbidden",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    return parser.parse_args()


def nonempty(value: Any) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def validate_screen(screen: Any, index: int, project_style: str) -> list[str]:
    prefix = f"screens[{index}]"
    errors: list[str] = []
    if not isinstance(screen, dict):
        return [f"{prefix} must be an object"]

    missing = sorted(REQUIRED_SCREEN_FIELDS - screen.keys())
    if missing:
        errors.append(f"{prefix} missing fields: {', '.join(missing)}")
        return errors

    allowed_empty = {"exact_copy", "connection_graph", "shared_axes", "entry_exit_ports"}
    for field in REQUIRED_SCREEN_FIELDS - allowed_empty:
        if not nonempty(screen[field]):
            errors.append(f"{prefix}.{field} must not be empty")

    screen_id = screen["screen_id"]
    if not isinstance(screen_id, str) or not re.fullmatch(r"\d{2}", screen_id):
        errors.append(f"{prefix}.screen_id must be a two-digit string")

    if screen["style_dna_id"] != project_style:
        errors.append(f"{prefix}.style_dna_id must match project style_dna_id")

    counts = screen["entity_count_exact"]
    if not isinstance(counts, dict) or not counts:
        errors.append(f"{prefix}.entity_count_exact must be a non-empty object")
    else:
        for entity, count in counts.items():
            if not isinstance(entity, str) or not entity.strip():
                errors.append(f"{prefix}.entity_count_exact contains an invalid entity name")
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                errors.append(f"{prefix}.entity_count_exact[{entity!r}] must be an integer >= 0")

    graph = screen["connection_graph"]
    if not isinstance(graph, list):
        errors.append(f"{prefix}.connection_graph must be an array")
    else:
        for edge_index, edge in enumerate(graph):
            if not isinstance(edge, dict) or not REQUIRED_CONNECTION_FIELDS <= edge.keys():
                errors.append(
                    f"{prefix}.connection_graph[{edge_index}] requires from, to, relation"
                )

    anchors = screen["anchor_positions"]
    if not isinstance(anchors, list):
        errors.append(f"{prefix}.anchor_positions must be an array")
    else:
        for anchor_index, anchor in enumerate(anchors):
            if not isinstance(anchor, dict) or not REQUIRED_ANCHOR_FIELDS <= anchor.keys():
                errors.append(
                    f"{prefix}.anchor_positions[{anchor_index}] requires entity, x, y, region"
                )
                continue
            for axis in ("x", "y"):
                value = anchor[axis]
                if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
                    errors.append(
                        f"{prefix}.anchor_positions[{anchor_index}].{axis} must be between 0 and 1"
                    )

    for field in (
        "exact_copy",
        "shared_axes",
        "entry_exit_ports",
        "primary_secondary_order",
        "protected_assets",
        "forbidden_entities",
        "forbidden_substitutions",
    ):
        if not isinstance(screen[field], list):
            errors.append(f"{prefix}.{field} must be an array")

    ports = screen["entry_exit_ports"]
    if isinstance(ports, list):
        for port_index, port in enumerate(ports):
            if not isinstance(port, dict) or not REQUIRED_PORT_FIELDS <= port.keys():
                errors.append(
                    f"{prefix}.entry_exit_ports[{port_index}] is missing continuity fields"
                )
                continue
            normalized_x = port["normalized_x"]
            if (
                not isinstance(normalized_x, (int, float))
                or isinstance(normalized_x, bool)
                or not 0 <= normalized_x <= 1
            ):
                errors.append(
                    f"{prefix}.entry_exit_ports[{port_index}].normalized_x "
                    "must be between 0 and 1"
                )

    if screen["status"] not in ALLOWED_INITIAL_STATUSES:
        errors.append(f"{prefix}.status is invalid")
    return errors


def main() -> None:
    args = parse_args()
    if not args.manifest.is_file():
        raise SystemExit(f"Manifest does not exist: {args.manifest}")

    try:
        payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read valid JSON: {exc}") from exc

    errors: list[str] = []
    if not isinstance(payload, dict):
        raise SystemExit("Manifest root must be an object")

    missing = sorted(REQUIRED_PROJECT_FIELDS - payload.keys())
    if missing:
        errors.append(f"Missing project fields: {', '.join(missing)}")
    if errors:
        raise SystemExit("\n".join(errors))

    if payload["page_type"] not in ALLOWED_PAGE_TYPES:
        errors.append(f"page_type must be one of: {', '.join(sorted(ALLOWED_PAGE_TYPES))}")
    if not isinstance(payload["style_dna_id"], str) or not payload["style_dna_id"].strip():
        errors.append("style_dna_id must be a non-empty string")
    screens = payload["screens"]
    if not isinstance(screens, list) or not screens:
        errors.append("screens must be a non-empty array")
    else:
        ids: list[str] = []
        for index, screen in enumerate(screens):
            errors.extend(validate_screen(screen, index, payload["style_dna_id"]))
            if isinstance(screen, dict) and isinstance(screen.get("screen_id"), str):
                ids.append(screen["screen_id"])
        if len(ids) != len(set(ids)):
            errors.append("screen_id values must be unique")

    if errors:
        raise SystemExit("Planning contract validation failed:\n- " + "\n- ".join(errors))

    print(
        json.dumps(
            {
                "valid": True,
                "project": payload["project"],
                "page_type": payload["page_type"],
                "screen_count": len(screens),
                "style_dna_id": payload["style_dna_id"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
