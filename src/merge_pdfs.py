#!/usr/bin/env python3
"""
merge_pdfs.py — Merge all PDF files in a directory into a single PDF document.

Features:
  - Natural sort order (file2.pdf before file10.pdf) or alphabetical/modified-time order
  - Recursive directory search (optional)
  - Per-file bookmarks/outline entries in the merged PDF (optional)
  - Skips corrupted/encrypted/unreadable PDFs gracefully and reports them
  - Dry-run mode to preview the merge order before writing anything
  - Clear logging and a non-zero exit code on failure

Usage:
  python merge_pdfs.py /path/to/pdf_folder
  python merge_pdfs.py /path/to/pdf_folder -o combined.pdf
  python merge_pdfs.py /path/to/pdf_folder --recursive --sort mtime
  python merge_pdfs.py /path/to/pdf_folder --bookmarks --dry-run

Requires: pypdf (pip install pypdf --break-system-packages)
"""

import argparse
import logging
import re
import sys
from pathlib import Path

try:
    from pypdf import PdfReader, PdfWriter
    from pypdf.errors import PdfReadError
except ImportError:
    print("Missing dependency 'pypdf'. Install it with:\n"
          "    pip install pypdf --break-system-packages", file=sys.stderr)
    sys.exit(1)


def natural_key(path: Path):
    """Sort key that treats embedded digits numerically (file2 < file10)."""
    return [
        int(chunk) if chunk.isdigit() else chunk.lower()
        for chunk in re.split(r"(\d+)", path.name)
    ]


def collect_pdfs(directory: Path, recursive: bool, sort_mode: str) -> list[Path]:
    pattern = "**/*.pdf" if recursive else "*.pdf"
    files = [p for p in directory.glob(pattern) if p.is_file()]

    if sort_mode == "name":
        files.sort(key=natural_key)
    elif sort_mode == "mtime":
        files.sort(key=lambda p: p.stat().st_mtime)
    elif sort_mode == "size":
        files.sort(key=lambda p: p.stat().st_size)

    return files


def merge_pdfs(files: list[Path], output_path: Path, add_bookmarks: bool,
               password: str | None) -> tuple[int, list[str]]:
    """Merge files into output_path. Returns (pages_written, skipped_files)."""
    writer = PdfWriter()
    skipped = []
    total_pages = 0

    for pdf_path in files:
        try:
            reader = PdfReader(str(pdf_path))

            if reader.is_encrypted:
                if password:
                    result = reader.decrypt(password)
                    if result == 0:
                        raise PdfReadError("incorrect password")
                else:
                    raise PdfReadError("file is encrypted, no password supplied")

            num_pages = len(reader.pages)
            if num_pages == 0:
                logging.warning("Skipping %s: contains 0 pages", pdf_path.name)
                skipped.append(f"{pdf_path.name} (0 pages)")
                continue

            start_page = total_pages
            for page in reader.pages:
                writer.add_page(page)
            total_pages += num_pages

            if add_bookmarks:
                writer.add_outline_item(pdf_path.stem, start_page)

            logging.info("Added %s (%d pages)", pdf_path.name, num_pages)

        except PdfReadError as e:
            logging.warning("Skipping %s: %s", pdf_path.name, e)
            skipped.append(f"{pdf_path.name} ({e})")
        except Exception as e:
            logging.warning("Skipping %s: unexpected error: %s", pdf_path.name, e)
            skipped.append(f"{pdf_path.name} (unexpected error: {e})")

    if total_pages == 0:
        raise RuntimeError("No pages were successfully read from any PDF; nothing to write.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)

    return total_pages, skipped


def parse_args():
    parser = argparse.ArgumentParser(
        description="Merge all PDF files in a directory into a single PDF document."
    )
    parser.add_argument("directory", type=Path, help="Directory containing PDF files")
    parser.add_argument("-o", "--output", type=Path, default=Path("merged.pdf"),
                         help="Output file path (default: merged.pdf)")
    parser.add_argument("--recursive", action="store_true",
                         help="Search subdirectories for PDFs too")
    parser.add_argument("--sort", choices=["name", "mtime", "size"], default="name",
                         help="Sort order for merging (default: name, natural sort)")
    parser.add_argument("--bookmarks", action="store_true",
                         help="Add a bookmark/outline entry for each source file")
    parser.add_argument("--password", default=None,
                         help="Password to try on encrypted PDFs")
    parser.add_argument("--dry-run", action="store_true",
                         help="Show the merge order without writing an output file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    return parser.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    directory = args.directory
    if not directory.is_dir():
        logging.error("Not a directory: %s", directory)
        sys.exit(1)

    files = collect_pdfs(directory, args.recursive, args.sort)
    if not files:
        logging.error("No PDF files found in %s", directory)
        sys.exit(1)

    logging.info("Found %d PDF file(s) to merge:", len(files))
    for i, f in enumerate(files, 1):
        logging.info("  %2d. %s", i, f.relative_to(directory))

    if args.dry_run:
        logging.info("Dry run complete — no output written.")
        return

    if args.output.resolve() in [f.resolve() for f in files]:
        logging.error("Output file would overwrite one of the input files. Choose a different --output.")
        sys.exit(1)

    try:
        total_pages, skipped = merge_pdfs(files, args.output, args.bookmarks, args.password)
    except RuntimeError as e:
        logging.error(str(e))
        sys.exit(1)

    logging.info("Wrote %s (%d pages) from %d/%d files",
                 args.output, total_pages, len(files) - len(skipped), len(files))

    if skipped:
        logging.warning("Skipped %d file(s):", len(skipped))
        for s in skipped:
            logging.warning("  - %s", s)


if __name__ == "__main__":
    main()