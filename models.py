"""
Data models for receipt parser application.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, validator


class ProcessingStatus(Enum):
    """Status of receipt processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class SummaryType(Enum):
    """Types of summary reports."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CATEGORY = "category"
    VENDOR = "vendor"
    YEARLY = "yearly"


@dataclass
class ReceiptItem:
    """Individual item from a receipt."""
    vendor: str
    amount: Decimal
    category: str = ""
    line_number: int = 0
    confidence: float = 1.0
    raw_text: str = ""

    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if self.amount < 0:
            raise ValueError(f"Amount cannot be negative: {self.amount}")

        self.vendor = self.vendor.strip()
        self.category = self.category.strip()

    @property
    def amount_float(self) -> float:
        """Get amount as float for compatibility."""
        return float(self.amount)


@dataclass
class Receipt:
    """Complete receipt data."""
    date: date
    items: List[ReceiptItem] = field(default_factory=list)
    source_file: Optional[Path] = None
    total_amount: Optional[Decimal] = None
    processing_time: Optional[float] = None
    extracted_text: str = ""

    def __post_init__(self):
        """Calculate derived fields."""
        if self.total_amount is None:
            self.total_amount = sum(item.amount for item in self.items)

    @property
    def total_float(self) -> float:
        """Get total as float for compatibility."""
        return float(self.total_amount) if self.total_amount else 0.0

    @property
    def item_count(self) -> int:
        """Number of items in receipt."""
        return len(self.items)

    def add_item(self, vendor: str, amount: Decimal, category: str = "", **kwargs) -> None:
        """Add an item to the receipt."""
        item = ReceiptItem(vendor=vendor, amount=amount, category=category, **kwargs)
        self.items.append(item)
        self.total_amount = sum(item.amount for item in self.items)


class ProcessingResult(BaseModel):
    """Result of receipt processing operation."""

    status: ProcessingStatus
    receipt: Optional[Receipt] = None
    error_message: Optional[str] = None
    processing_time: float = 0.0
    source_file: Optional[Path] = None
    extracted_text: str = ""

    class Config:
        arbitrary_types_allowed = True

    @validator('source_file')
    def validate_source_file(cls, v):
        if v is not None:
            return Path(v)
        return v

    @property
    def is_success(self) -> bool:
        """Check if processing was successful."""
        return self.status == ProcessingStatus.SUCCESS

    @property
    def has_data(self) -> bool:
        """Check if result contains receipt data."""
        return self.receipt is not None and len(self.receipt.items) > 0


@dataclass
class SummaryReport:
    """Summary report data."""
    summary_type: SummaryType
    period: str
    total_amount: Decimal
    item_count: int
    receipt_count: int
    breakdown: Dict[str, Decimal] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)

    @property
    def total_float(self) -> float:
        """Get total as float for compatibility."""
        return float(self.total_amount)

    @property
    def breakdown_float(self) -> Dict[str, float]:
        """Get breakdown as float dict for compatibility."""
        return {k: float(v) for k, v in self.breakdown.items()}

    @property
    def average_amount(self) -> Decimal:
        """Calculate average amount per receipt."""
        if self.receipt_count == 0:
            return Decimal("0.00")
        return self.total_amount / self.receipt_count


class ExportFormat(Enum):
    """Supported export formats."""
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    PDF = "pdf"


@dataclass
class ExportRequest:
    """Request for data export."""
    format: ExportFormat
    output_path: Path
    receipts: List[Receipt]
    include_summary: bool = True
    date_range: Optional[tuple] = None

    def __post_init__(self):
        """Validate export request."""
        if not self.receipts:
            raise ValueError("Cannot export empty receipt list")

        if self.output_path.suffix.lower() not in {".xlsx", ".csv", ".json", ".pdf"}:
            raise ValueError(f"Unsupported file extension: {self.output_path.suffix}")


class ValidationError(Exception):
    """Custom validation error."""

    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)


class ProcessingError(Exception):
    """Custom processing error."""

    def __init__(self, message: str, source_file: Optional[Path] = None):
        self.message = message
        self.source_file = source_file
        super().__init__(message)