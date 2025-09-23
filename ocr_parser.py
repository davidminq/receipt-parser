"""
OCR (Optical Character Recognition) module for extracting text from images.

This module provides a clean abstraction for OCR operations with proper error handling,
validation, and configuration support following SOLID principles.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any
from PIL import Image
import pytesseract

from config import settings
from models import ProcessingError, ValidationError
from utils.logging_setup import LoggerMixin, log_function_call


class OCRInterface(ABC):
    """Abstract interface for OCR implementations."""

    @abstractmethod
    def extract_text(self, image_path: Path, **kwargs) -> str:
        """Extract text from image.

        Args:
            image_path: Path to image file
            **kwargs: Additional OCR configuration

        Returns:
            Extracted text as string

        Raises:
            ValidationError: If image is invalid
            ProcessingError: If OCR processing fails
        """
        pass

    @abstractmethod
    def validate_image(self, image_path: Path) -> None:
        """Validate image file before processing.

        Args:
            image_path: Path to image file

        Raises:
            ValidationError: If image is invalid
        """
        pass


class ImageValidator(LoggerMixin):
    """Validates image files before OCR processing."""

    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.gif'}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MIN_FILE_SIZE = 100  # 100 bytes

    def validate(self, image_path: Path) -> None:
        """Comprehensive image validation.

        Args:
            image_path: Path to image file

        Raises:
            ValidationError: If validation fails
        """
        self.logger.debug("Validating image", path=str(image_path))

        self._validate_path_exists(image_path)
        self._validate_file_extension(image_path)
        self._validate_file_size(image_path)
        self._validate_image_format(image_path)

        self.logger.debug("Image validation successful", path=str(image_path))

    def _validate_path_exists(self, image_path: Path) -> None:
        """Check if file exists and is accessible."""
        if not image_path.exists():
            raise ValidationError(f"Image file not found: {image_path}", "file_path")

        if not image_path.is_file():
            raise ValidationError(f"Path is not a file: {image_path}", "file_path")

        if not image_path.stat().st_mode & 0o444:  # Check read permission
            raise ValidationError(f"No read permission for file: {image_path}", "file_path")

    def _validate_file_extension(self, image_path: Path) -> None:
        """Check if file extension is supported."""
        extension = image_path.suffix.lower()
        if extension not in self.SUPPORTED_FORMATS:
            raise ValidationError(
                f"Unsupported image format: {extension}. "
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}",
                "file_format"
            )

    def _validate_file_size(self, image_path: Path) -> None:
        """Check if file size is within acceptable limits."""
        file_size = image_path.stat().st_size

        if file_size < self.MIN_FILE_SIZE:
            raise ValidationError(
                f"File too small ({file_size} bytes). Minimum: {self.MIN_FILE_SIZE} bytes",
                "file_size"
            )

        if file_size > self.MAX_FILE_SIZE:
            raise ValidationError(
                f"File too large ({file_size} bytes). Maximum: {self.MAX_FILE_SIZE} bytes",
                "file_size"
            )

    def _validate_image_format(self, image_path: Path) -> None:
        """Validate image format by attempting to open with PIL."""
        try:
            with Image.open(image_path) as img:
                # Verify image can be loaded
                img.verify()

                # Re-open for additional checks (verify() closes the image)
                with Image.open(image_path) as img2:
                    # Check image dimensions
                    width, height = img2.size
                    if width < 10 or height < 10:
                        raise ValidationError(
                            f"Image too small: {width}x{height}. Minimum: 10x10 pixels",
                            "image_dimensions"
                        )

                    if width > 10000 or height > 10000:
                        raise ValidationError(
                            f"Image too large: {width}x{height}. Maximum: 10000x10000 pixels",
                            "image_dimensions"
                        )

        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Invalid image file: {str(e)}", "image_format")


class TesseractOCR(OCRInterface, LoggerMixin):
    """Tesseract-based OCR implementation."""

    def __init__(self, validator: Optional[ImageValidator] = None):
        """Initialize Tesseract OCR.

        Args:
            validator: Image validator instance
        """
        self.validator = validator or ImageValidator()
        self.config = settings.ocr
        self._setup_tesseract()

    def _setup_tesseract(self) -> None:
        """Configure Tesseract settings."""
        if self.config.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.config.tesseract_cmd

        self.logger.info(
            "Tesseract OCR initialized",
            tesseract_cmd=self.config.tesseract_cmd,
            language=self.config.language,
            psm_mode=self.config.psm_mode
        )

    def validate_image(self, image_path: Path) -> None:
        """Validate image using the configured validator."""
        self.validator.validate(image_path)

    @log_function_call
    def extract_text(self, image_path: Path, **kwargs) -> str:
        """Extract text from image using Tesseract.

        Args:
            image_path: Path to image file
            **kwargs: Additional OCR configuration

        Returns:
            Extracted text as string

        Raises:
            ValidationError: If image validation fails
            ProcessingError: If OCR processing fails
        """
        # Ensure Path object
        if isinstance(image_path, str):
            image_path = Path(image_path)

        self.logger.info("Starting OCR text extraction", path=str(image_path))

        # Validate image
        self.validate_image(image_path)

        try:
            # Build Tesseract configuration
            config = self._build_config(**kwargs)

            # Extract text
            with Image.open(image_path) as image:
                text = pytesseract.image_to_string(
                    image,
                    lang=self.config.language,
                    config=config
                )

            # Log results
            char_count = len(text)
            line_count = len(text.splitlines())

            self.logger.info(
                "OCR extraction completed",
                path=str(image_path),
                char_count=char_count,
                line_count=line_count,
                success=True
            )

            return text

        except pytesseract.TesseractError as e:
            self.logger.error("Tesseract processing failed", path=str(image_path), error=str(e))
            raise ProcessingError(f"OCR processing failed: {str(e)}", image_path)

        except Exception as e:
            self.logger.error("Unexpected OCR error", path=str(image_path), error=str(e))
            raise ProcessingError(f"Unexpected OCR error: {str(e)}", image_path)

    def _build_config(self, **kwargs) -> str:
        """Build Tesseract configuration string.

        Args:
            **kwargs: Additional configuration options

        Returns:
            Configuration string
        """
        psm_mode = kwargs.get('psm_mode', self.config.psm_mode)
        oem_mode = kwargs.get('oem_mode', self.config.oem_mode)
        config_options = kwargs.get('config_options', self.config.config_options)

        config_parts = [
            f"--psm {psm_mode}",
            f"--oem {oem_mode}"
        ]

        if config_options:
            config_parts.append(config_options)

        return " ".join(config_parts)


class OCRManager(LoggerMixin):
    """High-level OCR management with multiple backends support."""

    def __init__(self, ocr_impl: Optional[OCRInterface] = None):
        """Initialize OCR manager.

        Args:
            ocr_impl: OCR implementation to use
        """
        self.ocr_impl = ocr_impl or TesseractOCR()
        self.logger.info("OCR Manager initialized", implementation=type(self.ocr_impl).__name__)

    def extract_text_from_image(self, image_path: str | Path, **kwargs) -> str:
        """Extract text from image with comprehensive error handling.

        Args:
            image_path: Path to image file
            **kwargs: Additional OCR configuration

        Returns:
            Extracted text

        Raises:
            ValidationError: If image validation fails
            ProcessingError: If OCR processing fails
        """
        if isinstance(image_path, str):
            image_path = Path(image_path)

        return self.ocr_impl.extract_text(image_path, **kwargs)

    def batch_extract(self, image_paths: list[Path], **kwargs) -> Dict[Path, str]:
        """Extract text from multiple images.

        Args:
            image_paths: List of image paths
            **kwargs: Additional OCR configuration

        Returns:
            Dictionary mapping paths to extracted text
        """
        results = {}
        failed_count = 0

        self.logger.info("Starting batch OCR extraction", file_count=len(image_paths))

        for image_path in image_paths:
            try:
                text = self.extract_text_from_image(image_path, **kwargs)
                results[image_path] = text
            except (ValidationError, ProcessingError) as e:
                self.logger.error(
                    "Failed to process image in batch",
                    path=str(image_path),
                    error=str(e)
                )
                failed_count += 1
                results[image_path] = ""

        self.logger.info(
            "Batch OCR extraction completed",
            total_files=len(image_paths),
            successful=len(image_paths) - failed_count,
            failed=failed_count
        )

        return results


# Backward compatibility function
def extract_text_from_image(image_path: str | Path) -> str:
    """Legacy function for backward compatibility.

    Args:
        image_path: Path to image file

    Returns:
        Extracted text
    """
    manager = OCRManager()
    return manager.extract_text_from_image(image_path)


# Default OCR manager instance
ocr_manager = OCRManager()