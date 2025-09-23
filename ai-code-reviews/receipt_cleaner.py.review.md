# Code Review: receipt_cleaner.py

## Overview
**File**: `receipt_cleaner.py`
**Purpose**: Parse receipt text to extract item names and amounts using regex
**Lines of Code**: 21
**Overall Quality**: Needs Improvement
**Refactoring Effort**: Medium

## Issues Identified

### 🔴 Critical Issues

1. **SOLID Principle Violations** (Lines 3-22)
   - **Single Responsibility Principle**: Function handles text splitting, regex matching, data cleaning, and type conversion
   - **Open/Closed Principle**: Adding new receipt formats requires modifying this function
   - **Recommendation**: Extract separate classes for TextProcessor, RegexMatcher, and DataCleaner

2. **Fragile Regex Pattern** (Line 12)
   - **Issue**: Pattern `r"(.*?)(\$?\s?\d+\.\d{2})"` is too simplistic
   - **Problems**:
     - Won't match amounts without decimal places (e.g., "$5")
     - Won't match amounts with commas (e.g., "$1,234.56")
     - Captures unwanted text before amounts
     - No validation for reasonable amount ranges
   - **Recommendation**: Use more robust pattern and multiple validation steps

3. **Missing Type Hints** (Line 3)
   - **Issue**: No type annotations for parameter or return value
   - **Impact**: Poor IDE support and unclear interface
   - **Recommendation**: Add `def parse_receipt_text(text: str) -> List[Tuple[str, float]]:`

4. **Mixed Language Documentation** (Lines 4-6)
   - **Issue**: Korean comments in docstring
   - **Maintainability**: Inconsistent with international development standards
   - **Recommendation**: Use English for all documentation

### 🟡 Medium Issues

5. **No Input Validation** (Line 3)
   - **Issue**: No validation of input text parameter
   - **Impact**: Function fails on None or non-string inputs
   - **Recommendation**: Add input validation and type checking

6. **Silent Error Handling** (Lines 19-20)
   - **Issue**: `ValueError` exceptions are silently ignored with `continue`
   - **Impact**: No logging of parsing failures, makes debugging difficult
   - **Recommendation**: Log parsing failures and provide better error context

7. **No Configuration Options** (Lines 8-21)
   - **Issue**: Hardcoded regex pattern and processing logic
   - **Impact**: Cannot adapt to different receipt formats
   - **Recommendation**: Make patterns configurable or use strategy pattern

8. **Inefficient String Processing** (Line 14-15)
   - **Issue**: Multiple string operations on same data
   - **Impact**: Unnecessary processing overhead
   - **Recommendation**: Combine string cleaning operations

### 🟢 Minor Issues

9. **Magic Numbers** (Line 12)
   - **Issue**: Hardcoded decimal places requirement (`.d{2}`)
   - **Recommendation**: Make decimal precision configurable

10. **Variable Naming** (Line 9)
    - **Issue**: `cleaned_data` name doesn't clearly indicate tuple structure
    - **Recommendation**: Use `parsed_items` or `item_amount_pairs`

## Positive Aspects

- ✅ Clear function purpose and basic structure
- ✅ Appropriate use of regex for text parsing
- ✅ Good docstring with examples (though in Korean)
- ✅ Proper exception handling attempt
- ✅ Returns structured data format

## Recommended Refactoring

```python
import re
import logging
from typing import List, Tuple, Optional, Pattern
from dataclasses import dataclass

@dataclass
class ParsedItem:
    name: str
    amount: float
    line_number: int
    confidence: float = 1.0

class ReceiptPattern:
    """Encapsulates regex patterns for different receipt formats."""

    # More robust patterns
    AMOUNT_PATTERNS = [
        r"(.*?)\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*$",  # $1,234.56
        r"(.*?)\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*$",       # 1,234.56
        r"(.*?)\s*\$\s*(\d+(?:\.\d{1,2})?)\s*$",               # $123.4 or $123
    ]

    @classmethod
    def compile_patterns(cls) -> List[Pattern]:
        return [re.compile(pattern, re.IGNORECASE) for pattern in cls.AMOUNT_PATTERNS]

class ReceiptTextCleaner:
    """Handles cleaning and normalization of receipt text."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.patterns = ReceiptPattern.compile_patterns()

    def clean_item_name(self, name: str) -> str:
        """Clean and normalize item names."""
        return name.strip().replace('  ', ' ')

    def parse_amount(self, amount_str: str) -> float:
        """Parse amount string to float with validation."""
        cleaned = amount_str.replace('$', '').replace(',', '').strip()

        try:
            amount = float(cleaned)
            if amount < 0 or amount > 10000:  # Reasonable bounds
                raise ValueError(f"Amount out of reasonable range: {amount}")
            return amount
        except ValueError as e:
            self.logger.warning(f"Failed to parse amount '{amount_str}': {e}")
            raise

class ReceiptParser:
    """Main parser class following Single Responsibility Principle."""

    def __init__(self, cleaner: Optional[ReceiptTextCleaner] = None):
        self.cleaner = cleaner or ReceiptTextCleaner()
        self.logger = logging.getLogger(__name__)

    def parse_receipt_text(self, text: str) -> List[Tuple[str, float]]:
        """
        Parse receipt text to extract item names and amounts.

        Args:
            text: Raw receipt text from OCR

        Returns:
            List of (item_name, amount) tuples

        Raises:
            ValueError: If text is invalid
            TypeError: If text is not a string
        """
        if not isinstance(text, str):
            raise TypeError(f"Expected string, got {type(text)}")

        if not text.strip():
            return []

        lines = text.splitlines()
        parsed_items = []

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            item_data = self._parse_line(line, line_num)
            if item_data:
                parsed_items.append(item_data)

        return parsed_items

    def _parse_line(self, line: str, line_num: int) -> Optional[Tuple[str, float]]:
        """Parse a single line for item and amount."""
        for pattern in self.cleaner.patterns:
            match = pattern.search(line)
            if match:
                try:
                    item_name = self.cleaner.clean_item_name(match.group(1))
                    amount = self.cleaner.parse_amount(match.group(2))

                    if item_name and amount is not None:
                        return (item_name, amount)

                except ValueError as e:
                    self.logger.warning(f"Line {line_num}: {e}")
                    continue

        return None

# Backward compatibility
def parse_receipt_text(text: str) -> List[Tuple[str, float]]:
    """Legacy function for backward compatibility."""
    parser = ReceiptParser()
    return parser.parse_receipt_text(text)
```

## Security Considerations

- **Input Validation**: Validate text input to prevent injection attacks
- **Regex DoS**: Complex regex patterns can cause ReDoS attacks
- **Amount Validation**: Ensure parsed amounts are within reasonable bounds
- **Logging**: Avoid logging sensitive receipt data

## Performance Considerations

- Current regex approach is efficient for small texts
- For large texts, consider line-by-line processing
- Pattern compilation should be done once, not per call
- Consider caching compiled patterns

## Testing Gaps

- No unit tests present
- Need tests for various receipt formats
- Edge case testing (empty text, malformed amounts)
- Regex pattern validation tests
- Performance tests with large texts

## Compliance with Project Standards

- ❌ **SOLID Principles**: Single Responsibility Principle violation
- ❌ **PEP 8**: Missing type hints
- ❌ **Type Hints**: Completely missing
- ❌ **Docstrings**: Mixed language documentation
- ❌ **Error Handling**: Silent failure on parsing errors
- ✅ **Function Structure**: Clear and readable

## Action Items

1. **High Priority**: Refactor to follow SOLID principles
2. **High Priority**: Add comprehensive type hints
3. **High Priority**: Improve regex patterns for robustness
4. **High Priority**: Add proper input validation
5. **Medium Priority**: Implement better error handling and logging
6. **Medium Priority**: Make patterns configurable
7. **Low Priority**: Standardize documentation language

## Estimated Refactoring Effort: Medium (4-5 hours)