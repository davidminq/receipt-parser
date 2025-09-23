# Code Review: screenshot_watcher.py

## Overview
**File**: `screenshot_watcher.py`
**Purpose**: Unknown - file is empty
**Lines of Code**: 0
**Overall Quality**: Poor
**Refactoring Effort**: High (Complete Implementation Required)

## Issues Identified

### 🔴 Critical Issues

1. **Empty Implementation** (File is completely empty)
   - **Issue**: No code implementation present
   - **Impact**: Module exists but provides no functionality
   - **Recommendation**: Either implement the intended functionality or remove the file

2. **Missing Purpose Definition**
   - **Issue**: Based on filename, should watch for new screenshots but no specification exists
   - **Impact**: Unclear what directories to watch, what file types to monitor, what actions to take
   - **Recommendation**: Define requirements and implement file system monitoring

3. **No Module Documentation**
   - **Issue**: No docstring or comments explaining intended purpose
   - **Recommendation**: Add comprehensive module documentation

## Recommended Implementation

Based on the receipt parser context, this module likely should monitor directories for new screenshot files and automatically trigger receipt parsing. Here's a recommended implementation following SOLID principles:

```python
"""
Screenshot Watcher

This module provides functionality to monitor directories for new screenshot files
and automatically trigger receipt parsing when new images are detected.
"""

import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, List, Optional, Set
from dataclasses import dataclass
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
import logging

@dataclass
class WatchConfig:
    watch_directory: str
    file_extensions: Set[str]
    recursive: bool = True
    ignore_hidden: bool = True
    processing_delay: float = 1.0  # Delay to ensure file is fully written

class FileProcessor(ABC):
    @abstractmethod
    def process_file(self, file_path: str) -> bool:
        """Process a new file. Returns True if successful."""
        pass

class ReceiptImageProcessor(FileProcessor):
    """Processes receipt images using the existing parsing pipeline."""

    def __init__(self,
                 ocr_parser=None,
                 receipt_cleaner=None,
                 excel_writer=None):
        # Import here to avoid circular dependencies
        from ocr_parser import extract_text_from_image
        from receipt_cleaner import parse_receipt_text
        from excel_writer import save_to_excel
        from main import extract_date_from_text

        self.extract_text = ocr_parser or extract_text_from_image
        self.parse_receipt = receipt_cleaner or parse_receipt_text
        self.save_excel = excel_writer or save_to_excel
        self.extract_date = extract_date_from_text
        self.logger = logging.getLogger(__name__)

    def process_file(self, file_path: str) -> bool:
        """
        Process a receipt image file through the complete pipeline.

        Args:
            file_path: Path to the image file

        Returns:
            True if processing successful, False otherwise
        """
        try:
            self.logger.info(f"Processing receipt image: {file_path}")

            # Extract text using OCR
            text = self.extract_text(file_path)
            if not text.strip():
                self.logger.warning(f"No text extracted from {file_path}")
                return False

            # Extract receipt date
            receipt_date = self.extract_date(text)

            # Parse receipt items and amounts
            parsed_data = self.parse_receipt(text)
            if not parsed_data:
                self.logger.warning(f"No receipt data parsed from {file_path}")
                return False

            # Save to Excel
            self.save_excel(parsed_data, receipt_date)

            # Calculate and log summary
            total = sum(amount for _, amount in parsed_data)
            self.logger.info(f"Successfully processed {file_path}: {len(parsed_data)} items, ${total:.2f} total")

            return True

        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {e}")
            return False

class ScreenshotHandler(FileSystemEventHandler):
    """Handles file system events for screenshot monitoring."""

    def __init__(self,
                 config: WatchConfig,
                 processor: FileProcessor):
        self.config = config
        self.processor = processor
        self.logger = logging.getLogger(__name__)
        self._processing_queue: Set[str] = set()

    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return

        file_path = event.src_path
        if self._should_process_file(file_path):
            self.logger.info(f"New file detected: {file_path}")
            self._schedule_processing(file_path)

    def _should_process_file(self, file_path: str) -> bool:
        """Check if file should be processed based on configuration."""
        path = Path(file_path)

        # Check file extension
        if path.suffix.lower() not in self.config.file_extensions:
            return False

        # Check if hidden file (and we're ignoring them)
        if self.config.ignore_hidden and path.name.startswith('.'):
            return False

        # Check if already in processing queue
        if file_path in self._processing_queue:
            return False

        return True

    def _schedule_processing(self, file_path: str):
        """Schedule file for processing after a delay."""
        self._processing_queue.add(file_path)

        def delayed_process():
            time.sleep(self.config.processing_delay)
            try:
                success = self.processor.process_file(file_path)
                if success:
                    self.logger.info(f"Successfully processed: {file_path}")
                else:
                    self.logger.error(f"Failed to process: {file_path}")
            finally:
                self._processing_queue.discard(file_path)

        # In production, use threading.Thread or asyncio
        import threading
        thread = threading.Thread(target=delayed_process)
        thread.daemon = True
        thread.start()

class ScreenshotWatcher:
    """Main class for monitoring screenshot directories."""

    def __init__(self,
                 config: WatchConfig,
                 processor: Optional[FileProcessor] = None):
        self.config = config
        self.processor = processor or ReceiptImageProcessor()
        self.observer = Observer()
        self.logger = logging.getLogger(__name__)
        self._is_running = False

    def start_watching(self) -> None:
        """Start monitoring the configured directory."""
        if self._is_running:
            self.logger.warning("Watcher is already running")
            return

        # Validate watch directory
        watch_path = Path(self.config.watch_directory)
        if not watch_path.exists():
            raise FileNotFoundError(f"Watch directory does not exist: {self.config.watch_directory}")

        if not watch_path.is_dir():
            raise NotADirectoryError(f"Watch path is not a directory: {self.config.watch_directory}")

        # Setup event handler
        event_handler = ScreenshotHandler(self.config, self.processor)

        # Schedule observer
        self.observer.schedule(
            event_handler,
            self.config.watch_directory,
            recursive=self.config.recursive
        )

        # Start monitoring
        self.observer.start()
        self._is_running = True

        self.logger.info(f"Started watching directory: {self.config.watch_directory}")
        self.logger.info(f"Monitoring file types: {self.config.file_extensions}")

    def stop_watching(self) -> None:
        """Stop monitoring."""
        if not self._is_running:
            return

        self.observer.stop()
        self.observer.join()
        self._is_running = False
        self.logger.info("Stopped watching for screenshots")

    def watch_forever(self) -> None:
        """Start watching and block forever (until KeyboardInterrupt)."""
        try:
            self.start_watching()
            self.logger.info("Screenshot watcher started. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal, stopping...")
        finally:
            self.stop_watching()

def create_default_watcher(watch_directory: str = "screenshots") -> ScreenshotWatcher:
    """Create a screenshot watcher with default configuration."""
    config = WatchConfig(
        watch_directory=watch_directory,
        file_extensions={'.png', '.jpg', '.jpeg', '.tiff', '.bmp'},
        recursive=True,
        ignore_hidden=True,
        processing_delay=2.0
    )

    return ScreenshotWatcher(config)

def main():
    """Main entry point for standalone execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Watch directory for receipt screenshots")
    parser.add_argument(
        "--directory", "-d",
        default="screenshots",
        help="Directory to watch for screenshots (default: screenshots)"
    )
    parser.add_argument(
        "--extensions", "-e",
        nargs="+",
        default=[".png", ".jpg", ".jpeg"],
        help="File extensions to monitor (default: .png .jpg .jpeg)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create and start watcher
    config = WatchConfig(
        watch_directory=args.directory,
        file_extensions=set(args.extensions),
        recursive=True,
        ignore_hidden=True,
        processing_delay=2.0
    )

    watcher = ScreenshotWatcher(config)
    watcher.watch_forever()

if __name__ == "__main__":
    main()
```

## Dependencies Required

```python
# Add to requirements.txt
watchdog>=2.1.0  # For file system monitoring
```

## Integration with Existing Code

1. **Automatic Processing**: Integrates with existing OCR and Excel writing pipeline
2. **Configuration**: Allows customization of watch directories and file types
3. **Logging**: Comprehensive logging for monitoring and debugging
4. **Error Handling**: Robust error handling with graceful degradation

## Usage Examples

```python
# Basic usage
watcher = create_default_watcher("screenshots")
watcher.watch_forever()

# Custom configuration
config = WatchConfig(
    watch_directory="/Users/username/Desktop",
    file_extensions={'.png', '.jpg'},
    recursive=False,
    processing_delay=3.0
)
watcher = ScreenshotWatcher(config)
watcher.start_watching()
```

## Security Considerations

- **File Path Validation**: Ensure monitored files are within expected directories
- **Resource Limits**: Prevent processing of extremely large files
- **Permission Checks**: Validate read permissions before processing
- **Rate Limiting**: Prevent overwhelming system with too many simultaneous processes

## Performance Considerations

- **Threading**: Use proper threading for file processing to avoid blocking
- **Queue Management**: Implement proper queue for batch processing
- **Memory Usage**: Monitor memory usage with large image files
- **File Locking**: Handle files that are still being written

## Testing Strategy

- Unit tests for file filtering logic
- Integration tests with mock file system events
- Performance tests with large numbers of files
- Error condition testing (missing files, permission errors)

## Action Items

1. **High Priority**: Define specific requirements for file monitoring
2. **High Priority**: Implement basic file system watching capabilities
3. **High Priority**: Add integration with existing processing pipeline
4. **Medium Priority**: Add configuration options and command-line interface
5. **Medium Priority**: Implement proper threading and queue management
6. **Low Priority**: Add GUI interface for configuration

## Estimated Implementation Effort: High (10-15 hours)