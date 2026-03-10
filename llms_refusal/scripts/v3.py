import re
from pathlib import Path

def extract_table_rows(md_text):
    """
    Extract table rows from Markdown text.
    Returns a list for each row, ignoring headers and separator lines.
    """
    rows = []
    in_table = False
    for line in md_text.splitlines():
        if "|" in line:
            # Check if this is a table separator line
            if re.match(r"^\s*\|?[\s:-]+\|[\s|:-]*$", line):
                in_table = True
                continue
            if in_table:
                # Split cells and strip leading/trailing whitespace
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                rows.append(cells)
    return rows

def row_to_bool(row):
    """
    Determine whether a row contains a 'yes'-type value.
    """
    yes_patterns = re.compile(r"`?\*?yes\*?`?", re.IGNORECASE)
    for cell in row:
        if yes_patterns.search(cell):
            return "yes"
    return "no"

def merge_md_tables(file1, file2, output_file):
    md1 = Path(file1).read_text(encoding="utf-8")
    md2 = Path(file2).read_text(encoding="utf-8")
    
    rows1 = extract_table_rows(md1)
    rows2 = extract_table_rows(md2)
    
    # Ensure row counts are aligned
    max_len = max(len(rows1), len(rows2))
    rows1 += [[]] * (max_len - len(rows1))
    rows2 += [[]] * (max_len - len(rows2))
    
    merged_rows = []
    for r1, r2 in zip(rows1, rows2):
        print(r1, r2)
        combined_row = r1 + r2
        merged_rows.append([row_to_bool(r1), row_to_bool(r2)])
    print(merged_rows)
    
    count = 0
    c2 = 0
    c1 = 0
    for i, v in merged_rows:
        if i == v:
            count += 1
        if i == "yes":
            c2 += 1
        if v == "yes":
            c1 += 1

    print(count)
    # Write the new Markdown table
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("| v2 | v1 |\n")
        f.write("|----|----|\n")
        for row in merged_rows:
            f.write(f"| {row[0]} | {row[1]} |\n")
        f.write(f"Matches: {count}/30\n")
        f.write(f"Times deemed compliant by Model 1: {c1}/30\n")
        f.write(f"Times deemed compliant by Model 2: {c2}/30")
    print(f"Times Model 1 deemed Model 1 compliant: {c1}/30")
    print(f"Times Model 2 deemed Model 1 compliant: {c2}/30")

# Example usage
merge_md_tables(r".\check_prompt\v2.md", r".\check_prompt\v1.md", "cp1.md")
