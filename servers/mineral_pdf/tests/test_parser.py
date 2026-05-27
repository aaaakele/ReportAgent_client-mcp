"""
Tests for Mineral PDF MCP Server
"""

import io

import pytest

from servers.mineral_pdf.server import _detect_report_type, _find_float, _find_grade


def test_find_measured():
    patterns = [r"[Mm]easured\s*(?:[Rr]esources?)?\s*[:：]?\s*([\d,.]+)\s*(?:Mt|million\s*tonnes?)"]
    text = "Measured Resources: 12.5 Mt of lithium ore."
    result = _find_float(patterns, text)
    assert result == 12.5


def test_find_indicated():
    patterns = [r"[Ii]ndicated\s*(?:[Rr]esources?)?\s*[:：]?\s*([\d,.]+)\s*(?:Mt|million\s*tonnes?)"]
    text = "Indicated: 8,300 million tonnes"
    result = _find_float(patterns, text)
    assert result == 8300.0


def test_find_inferred():
    patterns = [r"[Ii]nferred\s*(?:[Rr]esources?)?\s*[:：]?\s*([\d,.]+)\s*(?:Mt|million\s*tonnes?)"]
    text = "Inferred resources: 5.2Mt"
    result = _find_float(patterns, text)
    assert result == 5.2


def test_find_grade():
    text = "Average grade: 1.52% Li2O"
    result = _find_grade(text)
    assert result == 1.52


def test_find_grade_alt_format():
    text = "Li2O %: 1.35%"
    result = _find_grade(text)
    assert result == 1.35


def test_detect_ni43101():
    assert _detect_report_type("This is a NI 43-101 compliant report") == "NI 43-101"


def test_detect_jorc():
    assert _detect_report_type("JORC Code 2012 Edition") == "JORC"


def test_detect_unknown():
    assert _detect_report_type("Some random text") == "Unknown"


def test_find_float_no_match():
    patterns = [r"Measured: ([\d,.]+) Mt"]
    result = _find_float(patterns, "No resources found")
    assert result == 0.0
