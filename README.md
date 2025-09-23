# Receipt Parser

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type Checked](https://img.shields.io/badge/type--checked-mypy-blue.svg)](http://mypy-lang.org/)

An enterprise-grade receipt parsing system that extracts itemized data from receipt images using OCR technology and exports to Excel format. Built with SOLID design principles and modern Python architecture patterns.

## Features

- **OCR Processing**: Extract text from receipt images using Tesseract with comprehensive validation
- **Intelligent Parsing**: Parse receipt text to identify vendor names and amounts using regex patterns
- **Excel Export**: Generate formatted Excel files with backup management and data preservation
- **Configuration Management**: Pydantic-based settings with environment variable support
- **Structured Logging**: Rich console output with file logging and execution tracking
- **Error Handling**: Comprehensive error management with custom exception classes
- **Modular Architecture**: SOLID principles implementation with dependency injection

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Tesseract OCR engine

### Installation

1. Clone the repository:
```bash
git clone https://github.com/davidminq/receipt-parser.git
cd receipt-parser
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Tesseract OCR:
- **macOS**: `brew install tesseract`
- **Ubuntu**: `sudo apt-get install tesseract-ocr`
- **Windows**: Download from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)

### Basic Usage

```python
from pathlib import Path
from receipt_parser import ReceiptProcessor

# Initialize processor
processor = ReceiptProcessor()

# Process a receipt image
receipt = processor.process_image(Path("receipt.jpg"))

# Export to Excel
processor.export_to_excel(receipt, Path("output.xlsx"))
```

## Architecture

The system follows SOLID design principles with a modular architecture:

### Core Components

- **OCR Module** (`ocr_parser.py`): Text extraction with validation and error handling
- **Parser Module** (`receipt_cleaner.py`): Intelligent text parsing with regex patterns
- **Excel Module** (`excel_writer.py`): Formatted Excel export with backup management
- **Models** (`models.py`): Data structures with validation using dataclasses and Pydantic
- **Configuration** (`config.py`): Settings management with type safety

### Design Patterns

- **Strategy Pattern**: Multiple parsing strategies for different receipt formats
- **Factory Pattern**: OCR and parser implementation selection
- **Dependency Injection**: Loose coupling between components
- **Template Method**: Standardized processing workflows

## Configuration

Configuration is managed through `config.py` with support for environment variables:

```python
# Environment variables (optional)
export OCR__TESSERACT_CMD="/usr/local/bin/tesseract"
export PARSING__MIN_AMOUNT="0.01"
export EXCEL__CREATE_BACKUP="true"
```

### Available Settings

- **OCR Configuration**: Tesseract parameters, language settings
- **Parsing Rules**: Amount patterns, validation limits, ignore words
- **Excel Export**: Column mappings, formatting, backup settings
- **Logging**: Log levels, file output, formatting options

## File Structure

```
receipt-parser/
├── config.py              # Configuration management
├── models.py               # Data models and validation
├── ocr_parser.py          # OCR processing module
├── receipt_cleaner.py     # Text parsing and cleaning
├── excel_writer.py        # Excel export functionality
├── utils/
│   └── logging_setup.py   # Structured logging configuration
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation
```

## Error Handling

The system implements comprehensive error handling:

- **ValidationError**: Input validation failures
- **ProcessingError**: OCR and parsing failures
- **Structured Logging**: Detailed error tracking with context

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Follow code style guidelines (Black formatting, type hints)
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

# 영수증 파서

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type Checked](https://img.shields.io/badge/type--checked-mypy-blue.svg)](http://mypy-lang.org/)

OCR 기술을 활용하여 영수증 이미지에서 항목별 데이터를 추출하고 Excel 형식으로 내보내는 엔터프라이즈급 영수증 파싱 시스템입니다. SOLID 설계 원칙과 현대적인 Python 아키텍처 패턴으로 구축되었습니다.

## 주요 기능

- **OCR 처리**: 포괄적인 검증과 함께 Tesseract를 사용한 영수증 이미지 텍스트 추출
- **지능형 파싱**: 정규식 패턴을 사용하여 업체명과 금액을 식별하는 영수증 텍스트 파싱
- **Excel 내보내기**: 백업 관리 및 데이터 보존 기능을 갖춘 형식화된 Excel 파일 생성
- **구성 관리**: 환경 변수 지원을 포함한 Pydantic 기반 설정
- **구조화된 로깅**: 파일 로깅 및 실행 추적을 포함한 Rich 콘솔 출력
- **오류 처리**: 사용자 정의 예외 클래스를 통한 포괄적인 오류 관리
- **모듈식 아키텍처**: 의존성 주입을 통한 SOLID 원칙 구현

## 빠른 시작

### 필수 요구 사항

- Python 3.8 이상
- Tesseract OCR 엔진

### 설치

1. 저장소 클론:
```bash
git clone https://github.com/davidminq/receipt-parser.git
cd receipt-parser
```

2. 의존성 설치:
```bash
pip install -r requirements.txt
```

3. Tesseract OCR 설치:
- **macOS**: `brew install tesseract`
- **Ubuntu**: `sudo apt-get install tesseract-ocr`
- **Windows**: [GitHub 릴리스](https://github.com/UB-Mannheim/tesseract/wiki)에서 다운로드

### 기본 사용법

```python
from pathlib import Path
from receipt_parser import ReceiptProcessor

# 프로세서 초기화
processor = ReceiptProcessor()

# 영수증 이미지 처리
receipt = processor.process_image(Path("receipt.jpg"))

# Excel로 내보내기
processor.export_to_excel(receipt, Path("output.xlsx"))
```

## 아키텍처

시스템은 모듈식 아키텍처와 함께 SOLID 설계 원칙을 따릅니다:

### 핵심 구성 요소

- **OCR 모듈** (`ocr_parser.py`): 검증 및 오류 처리를 포함한 텍스트 추출
- **파서 모듈** (`receipt_cleaner.py`): 정규식 패턴을 사용한 지능형 텍스트 파싱
- **Excel 모듈** (`excel_writer.py`): 백업 관리를 포함한 형식화된 Excel 내보내기
- **모델** (`models.py`): 데이터클래스와 Pydantic을 사용한 검증 포함 데이터 구조
- **구성** (`config.py`): 타입 안전성을 갖춘 설정 관리

### 설계 패턴

- **전략 패턴**: 다양한 영수증 형식에 대한 여러 파싱 전략
- **팩토리 패턴**: OCR 및 파서 구현 선택
- **의존성 주입**: 구성 요소 간 느슨한 결합
- **템플릿 메서드**: 표준화된 처리 워크플로

## 구성

구성은 환경 변수 지원과 함께 `config.py`를 통해 관리됩니다:

```python
# 환경 변수 (선택 사항)
export OCR__TESSERACT_CMD="/usr/local/bin/tesseract"
export PARSING__MIN_AMOUNT="0.01"
export EXCEL__CREATE_BACKUP="true"
```

### 사용 가능한 설정

- **OCR 구성**: Tesseract 매개변수, 언어 설정
- **파싱 규칙**: 금액 패턴, 검증 한계, 무시 단어
- **Excel 내보내기**: 열 매핑, 형식화, 백업 설정
- **로깅**: 로그 레벨, 파일 출력, 형식화 옵션

## 파일 구조

```
receipt-parser/
├── config.py              # 구성 관리
├── models.py               # 데이터 모델 및 검증
├── ocr_parser.py          # OCR 처리 모듈
├── receipt_cleaner.py     # 텍스트 파싱 및 정리
├── excel_writer.py        # Excel 내보내기 기능
├── utils/
│   └── logging_setup.py   # 구조화된 로깅 구성
├── requirements.txt       # Python 의존성
└── README.md              # 프로젝트 문서
```

## 오류 처리

시스템은 포괄적인 오류 처리를 구현합니다:

- **ValidationError**: 입력 검증 실패
- **ProcessingError**: OCR 및 파싱 실패
- **구조화된 로깅**: 컨텍스트를 포함한 상세한 오류 추적

## 기여

1. 저장소 포크
2. 기능 브랜치 생성: `git checkout -b feature-name`
3. 코드 스타일 가이드라인 준수 (Black 형식화, 타입 힌트)
4. 새로운 기능에 대한 테스트 추가
5. 풀 리퀘스트 제출

## 라이선스

이 프로젝트는 MIT 라이선스 하에 라이선스가 부여됩니다 - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.