#!/usr/bin/env python3
import argparse
import re
import subprocess
from pathlib import Path


def sips_dimension(path: Path) -> tuple[int, int]:
    out = subprocess.check_output(
        ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
        text=True,
        stderr=subprocess.DEVNULL,
    )
    width = int(re.search(r"pixelWidth:\s*(\d+)", out).group(1))
    height = int(re.search(r"pixelHeight:\s*(\d+)", out).group(1))
    return width, height


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)


def main() -> None:
    parser = argparse.ArgumentParser(description="Split a screenshot/image into overlapping vertical OCR segments, optionally upscaling each segment.")
    parser.add_argument("image", help="Input image path")
    parser.add_argument("--out-dir", required=True, help="Directory for segment images")
    parser.add_argument("--height", type=int, default=1400, help="Segment height in pixels")
    parser.add_argument("--overlap", type=int, default=180, help="Overlap between neighboring segments in pixels")
    parser.add_argument("--scale", type=float, default=2.0, help="Upscale factor for OCR, 1 disables scaling")
    args = parser.parse_args()

    image = Path(args.image)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    width, height = sips_dimension(image)
    step = max(1, args.height - args.overlap)
    y = 0
    idx = 1
    while y < height:
        crop_h = min(args.height, height - y)
        # sips crops from image center, so crop to the desired height first, then crop width.
        # For long screenshots intended for OCR, callers should first pass a tight image-only crop.
        temp = out_dir / f"segment_{idx:03d}_raw.png"
        final = out_dir / f"segment_{idx:03d}.png"
        # Create a top-aligned segment by cropping a shifted copy with ImageMagick if available;
        # fall back to screencapture-era tight crops using sips is less precise, but still useful.
        if subprocess.run(["which", "magick"], stdout=subprocess.DEVNULL).returncode == 0:
            run(["magick", str(image), "-crop", f"{width}x{crop_h}+0+{y}", str(temp)])
        elif subprocess.run(["which", "convert"], stdout=subprocess.DEVNULL).returncode == 0:
            run(["convert", str(image), "-crop", f"{width}x{crop_h}+0+{y}", str(temp)])
        else:
            # Last resort: copy whole image for the first segment only.
            if idx > 1:
                break
            run(["cp", str(image), str(temp)])

        if args.scale and args.scale != 1:
            seg_w, seg_h = sips_dimension(temp)
            run(["sips", "-z", str(int(seg_h * args.scale)), str(int(seg_w * args.scale)), str(temp), "--out", str(final)])
            temp.unlink(missing_ok=True)
        else:
            temp.rename(final)

        print(final)
        if y + crop_h >= height:
            break
        y += step
        idx += 1


if __name__ == "__main__":
    main()
