"""Standardized transformation process and error interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, Optional, Type

from jaclang.compiler.absyntree import AstNode, T
from jaclang.compiler.codeloc import CodeLocInfo
from jaclang.utils.log import logging


class Alert:
    """Alert interface."""

    def __init__(self, msg: str, loc: CodeLocInfo, from_pass: Type[Transform]) -> None:
        """Initialize alert."""
        self.msg = msg
        self.loc: CodeLocInfo = loc
        self.from_pass: Type[Transform] = from_pass

    def __str__(self) -> str:
        """Return string representation of alert."""
        return (
            f" {self.loc.mod_path}, line {self.loc.first_line},"
            f" col {self.loc.col_start}: {self.msg}"
        )

    def __repr__(self) -> str:
        """Return string representation of alert."""
        return self.as_log()

    def as_log(self) -> str:
        """Return the alert as a single line log as opposed to the pretty print."""
        file_path: str = self.loc.mod_path
        if file_path == "":
            return self.msg  # There are error messages without file references.

        line: int = self.loc.first_line
        column: int = self.loc.col_start
        return f"{file_path}:{line}:{column} {self.msg}"

    def pretty_print(self) -> str:
        """Pretty pritns the Alert to show the alert with source location."""
        return self.as_log() + self._dump_pretty_print_location()

    def _dump_pretty_print_location(self) -> str:
        """Pretty print internal method for the pretty_print method.

        Note that this wil return the string with the leading new line character
        if it contains any location alert info, otherwise it'll return empty
        string so the caller can just do a `+=`.
        """
        # NOTE: The Line numbers and the column numbers are starts with 1.
        # We print totally 5 lines (error line and above 2 and bellow 2).

        # The width of the line number we'll be printing (more of a settings).
        line_num_width: int = 5

        error_line = self.loc.first_line
        file_source: str = self.loc.file_source
        idx: int = self.loc.pos_start

        if file_source == "" or self.loc.mod_path == "":
            return ""

        start_line: int = error_line - 2
        if start_line < 1:
            start_line = 1
        end_line: int = start_line + 5  # Index is exclusive.

        # Get the first character of the [start_line].
        curr_line: int = error_line
        while idx > 0 and curr_line >= start_line:
            idx -= 1
            if idx == 0:
                break
            if file_source[idx] == "\n":
                curr_line -= 1

        assert idx == 0 or file_source[idx] == "\n"
        if idx != 0:
            idx += 1  # Enter the line.

        pretty_dump = ""

        # Print each lines.
        curr_line = start_line
        while curr_line < end_line:
            pretty_dump += f"%{line_num_width}d | " % curr_line

            idx_line_start = idx
            while idx < len(file_source) and file_source[idx] != "\n":
                idx += 1  # Run to the line end.
            pretty_dump += file_source[idx_line_start:idx]
            pretty_dump += "\n"

            if curr_line == error_line:  # Print the current line with indicator.
                pretty_dump += f"%{line_num_width}s | " % " "

                spaces = ""
                for idx_pre in range(idx_line_start, self.loc.pos_start):
                    spaces += "\t" if file_source[idx_pre] == "\t" else " "
                pretty_dump += spaces + "~\n"

            if idx == len(file_source):
                break
            curr_line += 1
            idx += 1

        return "\n" + pretty_dump


class Transform(ABC, Generic[T]):
    """Abstract class for IR passes."""

    def __init__(
        self,
        input_ir: T,
        prior: Optional[Transform] = None,
    ) -> None:
        """Initialize pass."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.errors_had: list[Alert] = [] if not prior else prior.errors_had
        self.warnings_had: list[Alert] = [] if not prior else prior.warnings_had
        self.cur_node: AstNode = input_ir  # tracks current node during traversal
        self.ir = self.transform(ir=input_ir)

    @abstractmethod
    def transform(self, ir: T) -> AstNode:
        """Transform interface."""
        pass

    def log_error(self, msg: str, node_override: Optional[AstNode] = None) -> None:
        """Pass Error."""
        alrt = Alert(
            msg,
            self.cur_node.loc if not node_override else node_override.loc,
            self.__class__,
        )
        self.errors_had.append(alrt)
        self.logger.error(alrt.as_log())

    def log_warning(self, msg: str, node_override: Optional[AstNode] = None) -> None:
        """Pass Error."""
        alrt = Alert(
            msg,
            self.cur_node.loc if not node_override else node_override.loc,
            self.__class__,
        )
        self.warnings_had.append(alrt)
        self.logger.warning(str(alrt))
