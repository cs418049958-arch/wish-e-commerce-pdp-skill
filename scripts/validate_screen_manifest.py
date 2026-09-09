#!/usr/bin/env python3
"""Validate PDP screen plans; structural fields are required only when relevant."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from typing import Any

PAGE_TYPES = {'long', 'short-grayboard', 'single'}
TASK_MODES = {'new', 'redesign', 'reuse', 'extend', 'edit', 'remove-copy'}
STATUSES = {'parsed', 'ready', 'generated', 'repair', 'qa_passed', 'user_approved', 'final', 'skipped',
            'contract_validated', 'style_locked', 'structure_passed', 'visual_passed', 'content_passed'}
POLICIES = {'direct-use', 'editable', 'reference', 'identity', 'approved-base', 'grayboard'}
CORE = {'screen_id', 'source_page_or_region', 'semantic_goal', 'exact_copy',
        'entity_count_exact', 'primary_secondary_order', 'style_dna_id', 'status'}
CONDITIONAL = {'connections': 'connection_graph', 'anchors': 'anchor_positions',
               'axes': 'shared_axes', 'ports': 'entry_exit_ports'}
PORT_FIELDS = {'continuity_group', 'object', 'from_screen', 'to_screen', 'edge_from', 'edge_to',
               'normalized_x', 'diameter_or_width_ratio', 'material', 'lighting', 'direction',
               'occlusion_forbidden'}


def nonblank(v: Any) -> bool:
    return isinstance(v, str) and bool(v.strip())


def strings(v: Any) -> bool:
    return isinstance(v, list) and all(nonblank(s) for s in v)


def ratio(v: Any, positive: bool = False) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and (0 < v <= 1 if positive else 0 <= v <= 1)


def choice(v: Any, choices: set[str]) -> bool:
    return isinstance(v, str) and v in choices


def validate_manifest(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ['Manifest root must be an object']
    errors: list[str] = []
    def check(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)
    version = payload.get('schema_version', 2)
    check(type(version) is int and version in (2, 3), 'schema_version must be 2 or 3')
    for field in ('project', 'style_dna_id'):
        check(nonblank(payload.get(field)), f'{field} must be a non-empty string')
    check(choice(payload.get('page_type'), PAGE_TYPES), 'page_type is invalid')
    if version == 3:
        check(choice(payload.get('task_mode'), TASK_MODES), 'task_mode is invalid')
        check(choice(payload.get('review_mode'), {'checkpoints', 'autonomous'}), 'review_mode is invalid')
    screens = payload.get('screens')
    if not isinstance(screens, list) or not screens:
        return errors + ['screens must be a non-empty array']
    ids, active_ids, all_ports = [], [], []
    for i, screen in enumerate(screens):
        p = f'screens[{i}]'
        if not isinstance(screen, dict):
            errors.append(f'{p} must be an object')
            continue
        sid = screen.get('screen_id')
        check(isinstance(sid, str) and re.fullmatch(r'[0-9]{2,}', sid) is not None,
              f'{p}.screen_id must be a numeric string with at least two digits')
        if isinstance(sid, str):
            ids.append(sid)
        check(nonblank(screen.get('source_page_or_region')), f'{p}.source_page_or_region is required')
        check(choice(screen.get('status'), STATUSES), f'{p}.status is invalid')
        if screen.get('status') == 'skipped':
            continue
        if isinstance(sid, str):
            active_ids.append(sid)
        check(CORE <= screen.keys(), f'{p} missing core fields: {sorted(CORE - screen.keys())}')
        check(nonblank(screen.get('semantic_goal')), f'{p}.semantic_goal is required')
        check(strings(screen.get('exact_copy')), f'{p}.exact_copy must be an array of strings')
        check(strings(screen.get('primary_secondary_order')) and bool(screen.get('primary_secondary_order')),
              f'{p}.primary_secondary_order must contain visual priorities')
        check(screen.get('style_dna_id') == payload.get('style_dna_id'), f'{p}.style_dna_id must match project')
        counts = screen.get('entity_count_exact')
        check(isinstance(counts, dict), f'{p}.entity_count_exact must be an object')
        if isinstance(counts, dict):
            for entity, count in counts.items():
                check(nonblank(entity) and type(count) is int and count >= 0, f'{p}.entity_count_exact[{entity!r}] is invalid')
        assets = screen.get('asset_plan', [] if version == 2 else None)
        check(isinstance(assets, list), f'{p}.asset_plan must be an array')
        if isinstance(assets, list):
            for j, asset in enumerate(assets):
                check(isinstance(asset, dict) and all(nonblank(asset.get(k)) for k in ('asset_id', 'source', 'role'))
                      and choice(asset.get('use_policy'), POLICIES), f'{p}.asset_plan[{j}] is invalid')
        requirements = screen.get('structural_requirements', [])
        check(strings(requirements), f'{p}.structural_requirements must be an array of strings')
        if strings(requirements):
            for requirement in requirements:
                check(requirement in CONDITIONAL, f'{p}: unknown structural requirement {requirement}')
                field = CONDITIONAL.get(requirement)
                if field:
                    check(isinstance(screen.get(field), list) and bool(screen.get(field)), f'{p}.{field} required for {requirement}')
        for field in CONDITIONAL.values():
            if field not in screen:
                continue
            values = screen[field]
            check(isinstance(values, list), f'{p}.{field} must be an array')
            if not isinstance(values, list):
                continue
            for j, value in enumerate(values):
                label = f'{p}.{field}[{j}]'
                if field == 'shared_axes':
                    check(strings(value) and len(value) >= 2, f'{label} needs at least two entity names')
                    continue
                if not isinstance(value, dict):
                    errors.append(f'{label} must be an object')
                    continue
                if field == 'connection_graph':
                    check(all(nonblank(value.get(k)) for k in ('from', 'to', 'relation')), f'{label} requires from, to, relation')
                elif field == 'anchor_positions':
                    check(all(nonblank(value.get(k)) for k in ('entity', 'region')) and
                          ratio(value.get('x')) and ratio(value.get('y')), f'{label} requires entity, region, x/y in [0,1]')
                else:
                    check(PORT_FIELDS <= value.keys(), f'{label} missing continuity fields')
                    for key in PORT_FIELDS - {'normalized_x', 'diameter_or_width_ratio', 'occlusion_forbidden'}:
                        check(nonblank(value.get(key)), f'{label}.{key} must be a non-empty string')
                    check(ratio(value.get('normalized_x')), f'{label}.normalized_x must be in [0,1]')
                    check(ratio(value.get('diameter_or_width_ratio'), True), f'{label}.diameter_or_width_ratio must be in (0,1]')
                    check(strings(value.get('occlusion_forbidden')), f'{label}.occlusion_forbidden must be an array of strings')
                    check(value.get('edge_from') == 'bottom' and value.get('edge_to') == 'top', f'{label} must connect bottom to top')
                    check(sid in (value.get('from_screen'), value.get('to_screen')), f'{label} must involve this screen')
                    all_ports.append((label, value))
        if 'final_file' in screen:
            f = screen['final_file']
            check(nonblank(f) and '/' not in f and '\\' not in f and f not in ('.', '..'), f'{p}.final_file must be a filename')
    check(len(ids) == len(set(ids)), 'screen_id values must be unique')
    order = payload.get('delivery_order', active_ids if version == 2 else None)
    if not strings(order) or not order:
        errors.append('delivery_order must be a non-empty array of screen IDs')
    else:
        check(len(order) == len(set(order)), 'delivery_order contains duplicates')
        check(set(order) == set(active_ids), 'delivery_order must contain exactly all non-skipped screens')
        for label, port in all_ports:
            a, b = port.get('from_screen'), port.get('to_screen')
            check(a in order and b in order and order.index(b) == order.index(a) + 1,
                  f'{label} must join adjacent delivered screens in order')
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.manifest.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise SystemExit(f'Cannot read manifest: {exc}') from exc
    errors = validate_manifest(payload)
    if errors:
        raise SystemExit('Screen manifest validation failed:\n- ' + '\n- '.join(errors))
    print(json.dumps({'valid': True, 'project': payload['project'], 'screen_count': len(payload['screens']),
                      'scope': 'Manifest only; image QA is separate'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
