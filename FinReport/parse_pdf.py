# Simple end-to-end: PDF -> Markdown (including tables) for the provided sample
# Outputs a single markdown file you can download.
import re, os, io, sys, subprocess, textwrap

import pdfplumber

def sanitize_cell(s):
    if s is None:
        return ""
    # Replace internal newlines/tabs with spaces; escape Markdown pipes
    s = str(s).replace("\r", " ").replace("\n", " ").replace("\t", " ")
    s = re.sub(r"\s+", " ", s).strip()
    s = s.replace("|", "\\|")
    return s

def table_to_markdown(rows):
    # Normalize rows to equal column count
    max_cols = max((len(r) for r in rows), default=0)
    norm = [(r + [""]*(max_cols-len(r))) for r in rows]
    norm = [[sanitize_cell(c) for c in r] for r in norm]
    if max_cols == 0 or len(norm) == 0:
        return ""
    # Use first row as header
    header = norm[0]
    body = norm[1:] if len(norm) > 1 else []
    md = []
    md.append("| " + " | ".join(header) + " |")
    md.append("| " + " | ".join("---" for _ in header) + " |")
    for r in body:
        md.append("| " + " | ".join(r) + " |")
    return "\n".join(md)

def extract_tables_from_page(page):
    tables = []
    # Strategy 1: text boundaries
    try:
        t1 = page.extract_tables(table_settings={"vertical_strategy":"text","horizontal_strategy":"text"})
        tables.extend(t1 or [])
    except Exception:
        pass
    # Strategy 2: line boundaries
    try:
        t2 = page.extract_tables(table_settings={"vertical_strategy":"lines","horizontal_strategy":"lines"})
        tables.extend(t2 or [])
    except Exception:
        pass
    # Clean/keep non-empty tables only
    cleaned = []
    for tbl in tables:
        if not tbl: 
            continue
        # strip rows that are completely empty
        keep = []
        for row in tbl:
            row = [("" if c is None else str(c)) for c in row]
            if any(cell.strip() for cell in row):
                keep.append(row)
        if keep:
            cleaned.append(keep)
    return cleaned

from utils.str_utils import convert_traditional_to_simplified

def pdf2md(PDF_PATH):
    md_lines = []
    with pdfplumber.open(PDF_PATH) as pdf:
        total = len(pdf.pages)
        md_lines.append(f"# PDF to Markdown export\n")
        md_lines.append(f"_Source_: `{os.path.basename(PDF_PATH)}`, _Pages_: {total}\n")
        for i, page in enumerate(pdf.pages, start=1):
            md_lines.append(f"\n\n---\n\n## Page {i}\n")
            # Tables
            tables = extract_tables_from_page(page)
            for ti, tbl in enumerate(tables, start=1):
                md_lines.append(f"\n**Table {ti}**\n\n")
                md_lines.append(table_to_markdown(tbl))
                md_lines.append("\n")
            # Text (after tables)
            text = page.extract_text() or ""
            if text.strip():
                # Convert to simple markdown paragraphs, preserve line breaks lightly
                text_md = text.replace("\r", "\n")
                # compress multiple blank lines
                text_md = re.sub(r"\n{3,}", "\n\n", text_md)
                md_lines.append("\n**Text**\n\n")
                md_lines.append(text_md)
    return convert_traditional_to_simplified("\n".join(md_lines))

