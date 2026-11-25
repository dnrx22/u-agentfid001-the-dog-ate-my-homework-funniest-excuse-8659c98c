#!/usr/bin/env python3
"""Emit the funniest homework excuse as a single line of text.

The program writes exactly one sentence to ``entry.txt`` inside the
output directory. The output is byte-for-byte deterministic: the same
input line always produces the same file, with no trailing newline and
no dependence on the clock, the environment, or the network.

Output directory resolution, in order:
  1. ``MAKEFUN_OUTPUT_DIR`` environment variable, when set and non-empty
  2. ``/output`` as the default
"""

import os
import sys
from pathlib import Path


EXCUSE = (
    "The homework looked at me first. I ate it in self-defense, "
    "and frankly, the quadratic formula tasted like betrayal."
)

FILENAME = "entry.txt"
DEFAULT_OUTPUT_DIR = "/output"
EXPECTED_LENGTH = 115


class ExcuseError(Exception):
    """Raised when the excuse or the output location is unusable."""


class ExcuseWriter:
    """Owns every step from checking the line to writing the file."""

    def __init__(self, line, output_dir):
        self.line = line
        self.output_dir = Path(output_dir)
        self.target = self.output_dir / FILENAME

    @classmethod
    def from_environment(cls, line):
        raw_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "")
        chosen = raw_dir.strip() or DEFAULT_OUTPUT_DIR
        return cls(line, chosen)

    def _rule_ends_with_full_stop(self):
        if not self.line.endswith("."):
            return "excuse must end with a full stop"
        if "?" in self.line or "!" in self.line:
            return "excuse must not contain ? or !"
        return None

    def _rule_no_extra_whitespace(self):
        if self.line != self.line.strip():
            return "excuse must not start or end with whitespace"
        if "\n" in self.line or "\r" in self.line or "\t" in self.line:
            return "excuse must not contain line breaks or tabs"
        return None

    def _rule_exact_length(self):
        if len(self.line) != EXPECTED_LENGTH:
            return (
                "excuse must be %d characters, got %d"
                % (EXPECTED_LENGTH, len(self.line))
            )
        return None

    def _rule_no_double_spaces(self):
        if "  " in self.line:
            return "excuse must not contain double spaces"
        return None

    def _rule_printable_ascii(self):
        bad = [ch for ch in self.line if ord(ch) < 32 or ord(ch) > 126]
        if bad:
            return "excuse must be printable ASCII only"
        return None

    def check_line(self):
        rules = (
            self._rule_ends_with_full_stop,
            self._rule_no_extra_whitespace,
            self._rule_exact_length,
            self._rule_no_double_spaces,
            self._rule_printable_ascii,
        )
        problems = []
        for rule in rules:
            message = rule()
            if message is not None:
                problems.append(message)
        if problems:
            raise ExcuseError("; ".join(problems))

    def prepare_directory(self):
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ExcuseError(
                "cannot create output directory %s: %s"
                % (self.output_dir, exc)
            ) from exc
        if not os.access(self.output_dir, os.W_OK):
            raise ExcuseError(
                "output directory %s is not writable" % self.output_dir
            )

    def write(self):
        payload = self.line.encode("utf-8")
        try:
            self.target.write_bytes(payload)
        except OSError as exc:
            raise ExcuseError(
                "cannot write %s: %s" % (self.target, exc)
            ) from exc
        return payload

    def confirm_written(self, payload):
        try:
            on_disk = self.target.read_bytes()
        except OSError as exc:
            raise ExcuseError(
                "cannot read back %s: %s" % (self.target, exc)
            ) from exc
        if on_disk != payload:
            raise ExcuseError(
                "written file %s does not match the excuse" % self.target
            )

    def run(self):
        self.check_line()
        self.prepare_directory()
        payload = self.write()
        self.confirm_written(payload)
        print("wrote %d bytes to %s" % (len(payload), self.target))
        return 0


def run():
    writer = ExcuseWriter.from_environment(EXCUSE)
    try:
        return writer.run()
    except ExcuseError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(run())
