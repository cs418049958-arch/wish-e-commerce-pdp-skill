#!/usr/bin/env python3
"""Validate and vertically stitch approved ecommerce detail-page screens."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from PIL import Image, ImageColor
from validate_screen_manifest import validate_manifest


SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def natural_key(path: Path) -> list[object]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", path.name)]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate equally wide screen images and stitch them into one long image."
    )
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--screen-manifest", type=Path, help="Select final files in explicit delivery order.")
    parser.add_argument("--width", type=int, help="Target width. Defaults to the first screen width.")
    parser.add_argument("--resize", action="store_true", help="Resize mismatched widths proportionally.")
    parser.add_argument("--gap", type=int, default=0, help="Pixels between screens. Default: 0.")
    parser.add_argument("--background", default="#FFFFFF", help="Canvas color used for RGB output.")
    return parser.parse_args()


def discover_images(input_dir: Path, output: Path) -> list[Path]:
    if not input_dir.is_dir():
        raise SystemExit(f"Input directory does not exist: {input_dir}")
    output_resolved = output.resolve()
    images = sorted(
        (
            path
            for path in input_dir.iterdir()
            if path.is_file()
            and path.suffix.lower() in SUPPORTED_EXTENSIONS
            and path.resolve() != output_resolved
        ),
        key=natural_key,
    )
    if not images:
        raise SystemExit(f"No supported screen images found in: {input_dir}")
    ids = []
    for path in images:
        match = re.match(r"^([0-9]{2,})(?:[-_.]|$)", path.stem)
        if not match:
            raise SystemExit(f"Screen filename must start with its numeric ID: {path.name}")
        ids.append(int(match.group(1)))
    if len(ids) != len(set(ids)):
        raise SystemExit("Duplicate screen IDs or alternate versions in input directory.")
    if ids != list(range(1, len(ids) + 1)):
        raise SystemExit("Missing or non-contiguous screen IDs; supply --screen-manifest for intentional exclusions.")
    return images


def select_from_manifest(input_dir: Path, output: Path, manifest: Path) -> list[Path]:
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"Cannot read screen manifest: {exc}") from exc
    errors = validate_manifest(payload)
    if errors:
        raise SystemExit("Invalid screen manifest:\n- " + "\n- ".join(errors))
    screens = {s["screen_id"]: s for s in payload["screens"] if s["status"] != "skipped"}
    order = payload.get("delivery_order", list(screens))
    root = input_dir.resolve()
    if not root.is_dir():
        raise SystemExit(f"Input directory does not exist: {input_dir}")
    paths = []
    for sid in order:
        screen = screens[sid]
        allowed = {"user_approved", "final"}
        if payload.get("review_mode") == "autonomous":
            allowed.add("qa_passed")
        if screen["status"] not in allowed:
            raise SystemExit(f"Screen {sid} is not ready for final delivery: {screen['status']}")
        filename = screen.get("final_file")
        if not isinstance(filename, str) or not filename:
            raise SystemExit(f"Screen {sid} needs final_file.")
        path = (root / filename).resolve()
        if path.parent != root or not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise SystemExit(f"Screen {sid} has missing or invalid final_file: {filename}")
        match = re.match(r"^([0-9]{2,})(?:[-_.]|$)", path.stem)
        if not match or int(match.group(1)) != int(sid):
            raise SystemExit(f"Screen {sid} final_file has a different screen ID: {filename}")
        if path == output.resolve():
            raise SystemExit("Output must not overwrite a source screen.")
        paths.append(path)
    if len(paths) != len(set(paths)):
        raise SystemExit("Multiple screens refer to the same final file.")
    extras = {p.resolve() for p in root.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS} - set(paths) - {output.resolve()}
    if extras:
        raise SystemExit("Unselected images in final directory: " + ", ".join(sorted(p.name for p in extras)))
    return paths


def load_and_normalize(
    paths: list[Path], target_width: int | None, allow_resize: bool
) -> tuple[list[Image.Image], list[dict[str, object]], int]:
    loaded: list[Image.Image] = []
    records: list[dict[str, object]] = []
    resolved_width = target_width

    for index, path in enumerate(paths, start=1):
        with Image.open(path) as source:
            source.load()
            original_width, original_height = source.size
            if resolved_width is None:
                resolved_width = original_width
            if resolved_width <= 0:
                raise SystemExit("Target width must be greater than zero.")

            image = source.convert("RGBA")
            resized = False
            if original_width != resolved_width:
                if not allow_resize:
                    raise SystemExit(
                        f"Width mismatch: {path.name} is {original_width}px; "
                        f"expected {resolved_width}px. Fix the source or rerun with --resize."
                    )
                new_height = max(1, round(original_height * resolved_width / original_width))
                image = image.resize((resolved_width, new_height), Image.Resampling.LANCZOS)
                resized = True

            loaded.append(image)
            records.append(
                {
                    "order": index,
                    "file": path.name,
                    "source_width": original_width,
                    "source_height": original_height,
                    "final_width": image.width,
                    "final_height": image.height,
                    "resized": resized,
                }
            )

    assert resolved_width is not None
    return loaded, records, resolved_width


def stitch(images: list[Image.Image], width: int, gap: int, background: str) -> Image.Image:
    if gap < 0:
        raise SystemExit("Gap cannot be negative.")
    rgb = ImageColor.getrgb(background)
    total_height = sum(image.height for image in images) + gap * (len(images) - 1)
    if total_height <= 0:
        raise SystemExit("Final height is invalid.")

    canvas = Image.new("RGBA", (width, total_height), (*rgb, 255))
    y = 0
    for image in images:
        canvas.alpha_composite(image, (0, y))
        y += image.height + gap
    return canvas


def save_output(canvas: Image.Image, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    suffix = output.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        canvas.convert("RGB").save(output, quality=95, subsampling=0, optimize=True)
    elif suffix == ".webp":
        canvas.save(output, lossless=True, method=6)
    else:
        if suffix != ".png":
            output = output.with_suffix(".png")
        canvas.save(output, optimize=True)
    return output


def main() -> None:
    args = parse_args()
    if args.output.suffix.lower() not in SUPPORTED_EXTENSIONS:
        args.output = args.output.with_suffix(".png")
    if args.screen_manifest and args.gap != 0:
        raise SystemExit("Final manifest-based stitching requires --gap 0.")
    paths = (select_from_manifest(args.input_dir, args.output, args.screen_manifest)
             if args.screen_manifest else discover_images(args.input_dir, args.output))
    if args.manifest and args.manifest.resolve() in {args.output.resolve(), *(p.resolve() for p in paths)}:
        raise SystemExit("Report path must not overwrite the output or source images.")
    if args.screen_manifest and args.manifest and args.screen_manifest.resolve() == args.manifest.resolve():
        raise SystemExit("Report path must not overwrite the screen manifest.")
    images, records, width = load_and_normalize(paths, args.width, args.resize)
    canvas = stitch(images, width, args.gap, args.background)
    args.output = save_output(canvas, args.output)

    payload = {
        "input_dir": str(args.input_dir.resolve()),
        "output": str(args.output.resolve()),
        "screen_count": len(images),
        "width": canvas.width,
        "height": canvas.height,
        "gap": args.gap,
        "background": args.background,
        "screens": records,
        "visual_qa": "not_evaluated_by_script",
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    Image.MAX_IMAGE_PIXELS = None
    main()
