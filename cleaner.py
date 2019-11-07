from os.path import isfile, join, exists
from typing import List, Tuple
from os import listdir, mkdir
from shutil import rmtree
import unicodedata as u
import csv
import re


OUTPUT_DIR = "output/"
ERROR_FILE = "Errors.txt"


def main():
    csv_list = find_files()
    prep_output()
    all_errors = []

    for path in csv_list:
        (header, rows) = read(path)
        (clean_header, clean_rows, errors) = clean(header, rows)
        all_errors += [error.format(path=path) for error in errors]
        if "E" not in [error[0] for error in errors]:
            write(path, clean_header, clean_rows)
    to_error_file(all_errors)


def find_files() -> List[str]:
    files = [f for f in listdir("./") if isfile(join("./", f))]
    csv_list = [f for f in files if re.search(r"\w+\.csv", f, re.IGNORECASE)]

    return csv_list


def prep_output():
    if exists(OUTPUT_DIR):
        rmtree(OUTPUT_DIR)

    if not exists(OUTPUT_DIR):
        mkdir(OUTPUT_DIR)


def read(link: str) -> Tuple[str, List[str]]:
    with open(link) as f:
        lines = f.readlines()
        lines = [line.replace("\n", "") for line in lines if line != "\n"]

    header = lines.pop(0)

    return header, lines


def clean(header: str, rows: List[str]) -> Tuple[List[str], List[List[str]], List[str]]:
    errors = []
    cleanup_funcs = [
        check_special_char,
        check_empty_col,
        check_empty_rows,
        check_commas,
        remove_not_ascii,
        remove_doubles,
    ]

    (col_num, sep) = get_header_info(header)

    header = header.split(sep)
    rows = [row.split(sep) for row in rows]

    for func in cleanup_funcs:
        (header, rows, error) = func(header, rows)
        errors += error

    return header, rows, errors


def get_header_info(header: str) -> Tuple[int, str]:
    sep = ";" if header.count(";") > header.count(",") else ","
    col_num = header.count(sep) + 1

    return col_num, sep


def check_empty_col(header: List[str], rows: List[List[str]]) -> Tuple[List[str], List[List[str]], List[str]]:
    error = []
    empty_h = [i for (i, col) in enumerate(header) if real_empty(col, i, rows)]

    if len(empty_h) != 0:
        error.append(f"WARNING: EmptyColumnWarning in file: {'{path}'}\n")

    for (i, row) in enumerate(rows):
        if len(row) != len(header):
            error.append(f"ERROR: ColumnNumberError in file: {'{path}'} \nLine: {i+2}\n")
            continue

        empty_h_val = [value for (i, value) in enumerate(row) if i in empty_h]
        if empty_h_val.count("") != len(empty_h):
            error.append(f"ERROR: EmptyColumnError in file: {'{path}'} \nLine: {i+2}\n")
            continue

        rows[i] = [val for (i, val) in enumerate(row) if i not in empty_h]

    clean_header = [col for (i, col) in enumerate(header) if i not in empty_h]
    clean_header = [col if col != "" else f"unnamed{i}" for i, col in enumerate(clean_header)]

    return clean_header, rows, error


def real_empty(col: str, i: int, rows: List[List[str]]) -> bool:
    if col != "":
        return False

    for row in rows:
        if row[i] != "":
            return False

    return True


def check_empty_rows(header: List[str], rows: List[List[str]]) -> Tuple[List[str], List[List[str]], List[str]]:
    error = []
    new_rows = []

    for i, row in enumerate(rows):
        if row.count("") == len(row):
            error.append(f"WARNING: EmptyRowWarning in file: {'{path}'} \nLine: {i+2}\n")
            continue
        new_rows.append(row)

    return header, new_rows, error


def check_commas(header: List[str], rows: List[List[str]]) -> Tuple[List[str], List[List[str]], List[str]]:
    error = []
    new_rows = []

    for row in rows:
        for (i, val) in enumerate(row):
            row[i] = val.replace(",", " ")
        new_rows.append(row)

    return header, new_rows, error


def remove_not_ascii(header: List[str], rows: List[List[str]]) -> Tuple[List[str], List[List[str]], List[str]]:
    error = []
    new_header = []

    for col in header:
        new_header.append(u.normalize('NFD', col).encode("ascii", "ignore").decode('ascii'))

    return new_header, rows, error


def check_special_char(header: List[str], rows: List[List[str]]) -> Tuple[List[str], List[List[str]], List[str]]:
    error = []
    new_header = []
    for col in header:
        col = col.strip()
        col = re.sub(r" ?#", "_no", col)
        new_header.append(re.sub(r"[^\w]", "", col))

    return new_header, rows, error


def remove_doubles(header: List[str], rows: List[List[str]]) -> Tuple[List[str], List[List[str]], List[str]]:
    error = []
    new_header = []
    mem = {}

    for col in header:
        if header.count(col) > 1:
            mem[col] = mem.get(col, 0) + 1
            new_header.append(col + str(mem[col]))
            if mem[col] == 1:
                error.append(f"WARNING: SameColumnNameWarning '{col}' in file: {'{path}'} \n")
        else:
            new_header.append(col)

    return new_header, rows, error


def write(path: str, clean_header: List[str], clean_rows: List[List[str]]) -> None:
    with open(OUTPUT_DIR + path, "w", encoding='utf8', newline='') as file:
        csv_file = csv.writer(file)
        csv_file.writerow(clean_header)
        csv_file.writerows(clean_rows)


def to_error_file(errors: List[str]):
    if len(errors) == 0:
        return

    with open(OUTPUT_DIR + ERROR_FILE, "a") as file:
        file.writelines([error for error in errors if error[0] == 'E'])
        file.write("\n")
        file.writelines([error for error in errors if error[0] == 'W'])


if __name__ == "__main__":
    main()
