"""
Receipt text parsing and cleaning module.

This module provides robust text parsing capabilities to extract item names and amounts
from OCR-processed receipt text, following SOLID principles with comprehensive error handling.
"""

import re
from abc import ABC, abstractmethod
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import List, Tuple, Optional, Pattern, Dict, Set
from dataclasses import dataclass

from config import settings
from models import ReceiptItem, ProcessingError, ValidationError
from utils.logging_setup import LoggerMixin, log_function_call


@dataclass
class ParsedLine:
    """Result of parsing a single line."""
    line_number: int
    raw_text: str
    vendor: str = ""
    amount: Optional[Decimal] = None
    confidence: float = 0.0
    parse_method: str = ""


class ParsingPattern:
    """Encapsulates regex patterns for different receipt formats."""

    def __init__(self, pattern: str, name: str, confidence: float = 1.0):
        """Initialize parsing pattern.

        Args:
            pattern: Regex pattern string
            name: Pattern name for identification
            confidence: Confidence level (0.0 to 1.0)
        """
        self.pattern = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
        self.name = name
        self.confidence = confidence

    def match(self, text: str) -> Optional[re.Match]:
        """Match pattern against text."""
        return self.pattern.search(text)


class PatternLibrary:
    """Library of receipt parsing patterns."""

    @classmethod
    def get_default_patterns(cls) -> List[ParsingPattern]:
        """Get default set of parsing patterns."""
        return [
            # High confidence patterns
            ParsingPattern(
                r"^(.+?)\s+\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2}))\s*$",
                "currency_with_commas",
                0.95
            ),
            ParsingPattern(
                r"^(.+?)\s+USD\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2}))\s*$",
                "usd_currency",
                0.95
            ),
            ParsingPattern(
                r"^(.+?)\s+\$(\d+\.\d{2})\s*$",
                "simple_currency",
                0.9
            ),

            # Medium confidence patterns
            ParsingPattern(
                r"^(.+?)\s+(\d{1,3}(?:,\d{3})*\.\d{2})\s*$",
                "decimal_amount",
                0.8
            ),
            ParsingPattern(
                r"^(.+?)\s+\$(\d+)\s*$",
                "whole_dollar",
                0.7
            ),

            # Lower confidence patterns
            ParsingPattern(
                r"(.+?)\s*[\$]?\s*(\d+\.?\d*)\s*$",
                "loose_numeric",
                0.5
            ),
        ]

    @classmethod
    def get_date_patterns(cls) -> List[ParsingPattern]:
        """Get date extraction patterns."""
        return [
            ParsingPattern(r"(\d{4}[-/]\d{2}[-/]\d{2})", "iso_date", 0.9),
            ParsingPattern(r"(\d{2}[-/]\d{2}[-/]\d{4})", "us_date", 0.8),
            ParsingPattern(r"(\d{1,2}[-/]\d{1,2}[-/]\d{4})", "flexible_date", 0.7),
        ]


class TextCleaner(LoggerMixin):
    """Handles text cleaning and normalization."""

    def __init__(self):
        """Initialize text cleaner."""
        self.ignore_words = settings.parsing.ignore_words

    def clean_line(self, line: str) -> str:
        """Clean and normalize a single line.

        Args:
            line: Raw line text

        Returns:
            Cleaned line text
        """
        if not line:
            return ""

        # Remove extra whitespace
        cleaned = " ".join(line.split())

        # Remove common noise characters
        cleaned = re.sub(r'[^\w\s\$\.\,\-]', '', cleaned)

        # Normalize currency symbols
        cleaned = re.sub(r'\$+', '$', cleaned)

        return cleaned.strip()

    def clean_vendor_name(self, vendor: str) -> str:
        """Clean and normalize vendor name.

        Args:
            vendor: Raw vendor name

        Returns:
            Cleaned vendor name
        """
        if not vendor:
            return ""

        # Remove extra whitespace
        cleaned = " ".join(vendor.split())

        # Remove trailing punctuation
        cleaned = re.sub(r'[^\w\s]+$', '', cleaned)

        # Remove leading numbers/symbols
        cleaned = re.sub(r'^[\d\W]+', '', cleaned)

        # Title case
        cleaned = cleaned.title()

        return cleaned.strip()

    def should_ignore_line(self, line: str) -> bool:
        """Check if line should be ignored based on content.

        Args:
            line: Line to check

        Returns:
            True if line should be ignored
        """
        line_lower = line.lower()

        # Ignore empty lines
        if not line.strip():
            return True

        # Ignore lines with only numbers or symbols
        if re.match(r'^[\d\W\s]+$', line):
            return True

        # Ignore lines containing ignore words
        for word in self.ignore_words:
            if word in line_lower:
                return True

        # Ignore very short lines (likely noise)
        if len(line.strip()) < 3:
            return True

        return False


class AmountParser(LoggerMixin):
    """Handles parsing and validation of monetary amounts."""

    def __init__(self):
        """Initialize amount parser."""
        self.min_amount = Decimal(str(settings.parsing.min_amount))
        self.max_amount = Decimal(str(settings.parsing.max_amount))

    def parse_amount(self, amount_str: str) -> Decimal:
        """Parse amount string to Decimal with validation.

        Args:
            amount_str: Amount string to parse

        Returns:
            Parsed amount as Decimal

        Raises:
            ValidationError: If amount is invalid
        """
        if not amount_str:
            raise ValidationError("Empty amount string", "amount")

        # Clean amount string
        cleaned = self._clean_amount_string(amount_str)

        try:
            amount = Decimal(cleaned)
        except InvalidOperation:
            raise ValidationError(f"Invalid amount format: {amount_str}", "amount")

        # Validate range
        if amount < self.min_amount:
            raise ValidationError(
                f"Amount too small: {amount}. Minimum: {self.min_amount}",
                "amount_range"
            )

        if amount > self.max_amount:
            raise ValidationError(
                f"Amount too large: {amount}. Maximum: {self.max_amount}",
                "amount_range"
            )

        return amount

    def _clean_amount_string(self, amount_str: str) -> str:
        """Clean amount string for parsing."""
        # Remove currency symbols and whitespace
        cleaned = amount_str.replace('$', '').replace('USD', '').strip()

        # Remove commas from thousands separators
        cleaned = cleaned.replace(',', '')

        # Handle missing decimal point for cents
        if '.' not in cleaned and len(cleaned) > 2:
            # Check if last two digits might be cents
            if cleaned[-2:].isdigit() and len(cleaned) > 2:
                # Only if there's a clear separation (e.g., "1234" -> "12.34")
                if len(cleaned) <= 4:
                    cleaned = cleaned[:-2] + '.' + cleaned[-2:]

        return cleaned


class ReceiptParserInterface(ABC):
    """Abstract interface for receipt parsing implementations."""

    @abstractmethod
    def parse_receipt_text(self, text: str) -> List[ReceiptItem]:
        """Parse receipt text to extract items.

        Args:
            text: Raw receipt text

        Returns:
            List of parsed receipt items
        """
        pass


class RegexReceiptParser(ReceiptParserInterface, LoggerMixin):
    """Regex-based receipt parser implementation."""

    def __init__(self,
                 patterns: Optional[List[ParsingPattern]] = None,
                 text_cleaner: Optional[TextCleaner] = None,
                 amount_parser: Optional[AmountParser] = None):
        """Initialize regex parser.

        Args:
            patterns: List of parsing patterns
            text_cleaner: Text cleaning instance
            amount_parser: Amount parsing instance
        """
        self.patterns = patterns or PatternLibrary.get_default_patterns()
        self.text_cleaner = text_cleaner or TextCleaner()
        self.amount_parser = amount_parser or AmountParser()

    @log_function_call
    def parse_receipt_text(self, text: str) -> List[ReceiptItem]:
        """Parse receipt text using regex patterns.

        Args:
            text: Raw receipt text from OCR

        Returns:
            List of parsed receipt items

        Raises:
            ValidationError: If text is invalid
        """
        if not isinstance(text, str):
            raise ValidationError(f"Expected string, got {type(text)}", "text_type")

        if not text.strip():
            self.logger.warning("Empty receipt text provided")
            return []

        lines = text.splitlines()
        parsed_items = []
        successful_parses = 0

        self.logger.info("Starting receipt parsing", line_count=len(lines))

        for line_num, line in enumerate(lines, 1):
            try:
                parsed_line = self._parse_line(line, line_num)
                if parsed_line and parsed_line.amount is not None:
                    item = ReceiptItem(
                        vendor=parsed_line.vendor,
                        amount=parsed_line.amount,
                        line_number=parsed_line.line_number,
                        confidence=parsed_line.confidence,
                        raw_text=parsed_line.raw_text
                    )
                    parsed_items.append(item)
                    successful_parses += 1

            except ValidationError as e:
                self.logger.warning(
                    "Failed to parse line",
                    line_number=line_num,
                    line=line,
                    error=str(e)
                )
                continue

        self.logger.info(
            "Receipt parsing completed",
            total_lines=len(lines),
            successful_parses=successful_parses,
            items_found=len(parsed_items)
        )

        return parsed_items

    def _parse_line(self, line: str, line_num: int) -> Optional[ParsedLine]:
        """Parse a single line for item and amount.

        Args:
            line: Line text to parse
            line_num: Line number for tracking

        Returns:
            ParsedLine object or None if parsing failed
        """
        # Clean the line
        cleaned_line = self.text_cleaner.clean_line(line)

        # Check if line should be ignored
        if self.text_cleaner.should_ignore_line(cleaned_line):
            return None

        # Try each pattern in order of confidence
        for pattern in sorted(self.patterns, key=lambda p: p.confidence, reverse=True):
            match = pattern.match(cleaned_line)
            if match:
                try:
                    vendor_raw = match.group(1)
                    amount_raw = match.group(2)

                    # Clean vendor name
                    vendor = self.text_cleaner.clean_vendor_name(vendor_raw)
                    if not vendor:
                        continue

                    # Parse amount
                    amount = self.amount_parser.parse_amount(amount_raw)

                    return ParsedLine(
                        line_number=line_num,
                        raw_text=line,
                        vendor=vendor,
                        amount=amount,
                        confidence=pattern.confidence,
                        parse_method=pattern.name
                    )

                except ValidationError as e:
                    self.logger.debug(
                        "Pattern match failed validation",
                        pattern=pattern.name,
                        line=cleaned_line,
                        error=str(e)
                    )
                    continue

        return None


class ReceiptParsingManager(LoggerMixin):
    """High-level receipt parsing management."""

    def __init__(self, parser: Optional[ReceiptParserInterface] = None):
        """Initialize parsing manager.

        Args:
            parser: Parser implementation to use
        """
        self.parser = parser or RegexReceiptParser()
        self.logger.info("Receipt parsing manager initialized")

    def parse_receipt_text(self, text: str) -> List[ReceiptItem]:
        """Parse receipt text with comprehensive error handling.

        Args:
            text: Receipt text to parse

        Returns:
            List of parsed receipt items

        Raises:
            ProcessingError: If parsing fails
        """
        try:
            return self.parser.parse_receipt_text(text)
        except ValidationError as e:
            raise ProcessingError(f"Receipt parsing validation failed: {str(e)}")
        except Exception as e:
            self.logger.error("Unexpected parsing error", error=str(e))
            raise ProcessingError(f"Unexpected parsing error: {str(e)}")

    def parse_receipt_file(self, file_path: Path) -> List[ReceiptItem]:
        """Parse receipt from text file.

        Args:
            file_path: Path to text file

        Returns:
            List of parsed receipt items
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            return self.parse_receipt_text(text)
        except FileNotFoundError:
            raise ProcessingError(f"Receipt file not found: {file_path}")
        except Exception as e:
            raise ProcessingError(f"Failed to read receipt file: {str(e)}")


# Backward compatibility function
def parse_receipt_text(text: str) -> List[Tuple[str, float]]:
    """Legacy function for backward compatibility.

    Args:
        text: Receipt text to parse

    Returns:
        List of (vendor, amount) tuples
    """
    manager = ReceiptParsingManager()
    items = manager.parse_receipt_text(text)
    return [(item.vendor, item.amount_float) for item in items]


# Default parsing manager instance
parsing_manager = ReceiptParsingManager()