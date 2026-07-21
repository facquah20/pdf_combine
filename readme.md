# merge_pdfs.py

A robust command-line tool for merging every PDF in a directory into a single PDF document.

## Features

- **Natural sort order** — `file2.pdf` is merged before `file10.pdf` (not the reverse, which plain alphabetical sorting would produce)
- **Flexible ordering** — sort by name, last-modified time, or file size
- **Recursive search** — optionally include PDFs in subdirectories
- **Bookmarks** — optionally add a clickable outline entry for each source file in the merged PDF
- **Encrypted PDF support** — supply a password to decrypt and include protected files
- **Fault-tolerant** — corrupted, empty, or unreadable PDFs are skipped (not fatal) and reported in a summary instead of crashing the whole run
- **Dry-run mode** — preview the exact merge order before writing any output
- **Safety check** — refuses to let the output file overwrite one of the inputs

## Requirements

- Python 3.9+
- [pypdf](https://pypi.org/project/pypdf/)

Install the dependency:

```bash
pip install pypdf --break-system-packages
```

(Drop `--break-system-packages` if you're using a virtual environment.)

## Usage

```bash
python merge_pdfs.py <directory> [options]
```

### Basic example

```bash
python merge_pdfs.py ./reports
```

Merges every `.pdf` in `./reports` (natural name order) into `merged.pdf` in the current directory.

### Options

| Flag | Description | Default |
|---|---|---|
| `-o`, `--output PATH` | Output file path | `merged.pdf` |
| `--recursive` | Include PDFs in subdirectories | off |
| `--sort {name,mtime,size}` | Merge order: natural filename sort, last-modified time, or file size | `name` |
| `--bookmarks` | Add a bookmark/outline entry per source file | off |
| `--password PASSWORD` | Password to try on encrypted PDFs | none |
| `--dry-run` | Print the merge order without writing a file | off |
| `-v`, `--verbose` | Verbose (debug-level) logging | off |

### More examples

Custom output name:
```bash
python merge_pdfs.py ./invoices -o all_invoices.pdf
```

Include subfolders, sorted by date modified:
```bash
python merge_pdfs.py ./scans --recursive --sort mtime
```

Add per-file bookmarks and preview first:
```bash
python merge_pdfs.py ./chapters --bookmarks --dry-run
```

Merge password-protected PDFs:
```bash
python merge_pdfs.py ./contracts --password "s3cret"
```

## How it handles problems

- **No PDFs found** → exits with an error message, nothing is written.
- **A PDF is corrupted, empty, or fails to open** → it's skipped, a warning is logged, and it's listed in the end-of-run summary. The rest of the merge still completes.
- **A PDF is encrypted and no/wrong password is given** → it's skipped and reported, same as above.
- **All PDFs fail to read** → the script stops and exits with an error rather than writing an empty output file.
- **Output path matches one of the inputs** → the script exits before writing anything, so you never accidentally overwrite a source file.

## Exit codes

- `0` — success
- `1` — no PDFs found, invalid directory, output would overwrite an input, or every input failed to read

## License

Free to use and modify.