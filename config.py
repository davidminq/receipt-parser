"""
Configuration management for receipt parser application.
"""

from pathlib import Path
from typing import List, Optional, Set
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings


class OCRConfig(BaseModel):
    """OCR processing configuration."""

    tesseract_cmd: Optional[str] = None
    psm_mode: int = Field(default=6, ge=0, le=13)
    oem_mode: int = Field(default=3, ge=0, le=3)
    language: str = "eng"
    config_options: str = ""

    @validator('tesseract_cmd')
    def validate_tesseract_path(cls, v):
        if v and not Path(v).exists():
            raise ValueError(f"Tesseract executable not found: {v}")
        return v


class ParsingConfig(BaseModel):
    """Receipt parsing configuration."""

    # Amount patterns for different formats
    amount_patterns: List[str] = Field(default=[
        r"(.*?)\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*$",  # $1,234.56
        r"(.*?)\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*$",       # 1,234.56
        r"(.*?)\s*\$\s*(\d+(?:\.\d{1,2})?)\s*$",               # $123.4
    ])

    # Date patterns
    date_patterns: List[str] = Field(default=[
        r"\d{4}[-/]\d{2}[-/]\d{2}",  # YYYY-MM-DD or YYYY/MM/DD
        r"\d{2}[-/]\d{2}[-/]\d{4}",  # MM-DD-YYYY or MM/DD/YYYY
        r"\d{1,2}[-/]\d{1,2}[-/]\d{4}",  # M-D-YYYY
    ])

    # Validation limits
    min_amount: float = Field(default=0.01, gt=0)
    max_amount: float = Field(default=10000.0, gt=0)

    # Item name cleaning
    ignore_words: Set[str] = Field(default={
        "tax", "total", "subtotal", "tip", "gratuity",
        "discount", "coupon", "credit", "change"
    })


class ExcelConfig(BaseModel):
    """Excel export configuration."""

    default_filename: str = "receipts.xlsx"
    sheet_name_format: str = "Receipt {date}"

    # Column configuration
    columns: dict = Field(default={
        "date": "날짜",
        "vendor": "업체명",
        "category": "카테고리",
        "amount": "금액 ($)"
    })

    # Formatting
    currency_format: str = "$#,##0.00"
    date_format: str = "YYYY-MM-DD"

    # Backup settings
    create_backup: bool = True
    max_backup_files: int = 10


class WatcherConfig(BaseModel):
    """File watcher configuration."""

    watch_directory: Path = Field(default=Path("screenshots"))
    file_extensions: Set[str] = Field(default={".png", ".jpg", ".jpeg", ".tiff", ".bmp"})
    recursive: bool = True
    ignore_hidden: bool = True
    processing_delay: float = Field(default=2.0, gt=0)

    @validator('watch_directory')
    def validate_watch_directory(cls, v):
        return Path(v)


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[Path] = None
    max_file_size: int = Field(default=10 * 1024 * 1024)  # 10MB
    backup_count: int = 5


class AppSettings(BaseSettings):
    """Main application settings."""

    # Sub-configurations
    ocr: OCRConfig = Field(default_factory=OCRConfig)
    parsing: ParsingConfig = Field(default_factory=ParsingConfig)
    excel: ExcelConfig = Field(default_factory=ExcelConfig)
    watcher: WatcherConfig = Field(default_factory=WatcherConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    # Global settings
    project_root: Path = Field(default=Path.cwd())
    data_directory: Path = Field(default=Path("data"))
    temp_directory: Path = Field(default=Path("temp"))

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure required directories exist."""
        for directory in [self.data_directory, self.temp_directory, self.watcher.watch_directory]:
            directory.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = AppSettings()