"""
CSV reader.
"""

from __future__ import annotations

import csv
from pathlib import Path


class CsvTable:
    """
    CSV rows with a header located by its first cell.
    """

    def __init__(self, path: Path, header_marker: str):
        self.path = path
        self.header_marker = header_marker

        with path.open(newline="") as f:
            self.rows = list(csv.reader(f))

        self.header_row_index = self.__header_row_index(self.header_marker)

    def __header_row_index(self, first_cell: str) -> int:
        """
        Look up the row number of header row.

        Args:
            first_cell (str): the first column of header row to match.

        Example:
            # comment row
            year,month,day ... # header row

            in this example, pass the first cell of the header row "year"

        """
        target = first_cell.strip().lower()

        for index, row in enumerate(self.rows):
            if row and row[0].strip().lower() == target:
                return index

        raise ValueError(f"No {first_cell!r} header in {self.path}")

    def data_rows(self) -> list[list[str]]:
        return self.rows[self.header_row_index + 1 :]

    def dict_rows(self) -> list[dict[str, str]]:
        header = [cell.strip() for cell in self.rows[self.header_row_index]]
        return [dict(zip(header, row)) for row in self.rows[self.header_row_index + 1 :] if row]
