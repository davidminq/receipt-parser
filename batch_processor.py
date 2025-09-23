#!/usr/bin/env python3
"""
여러 영수증 이미지를 일괄 처리하는 배치 프로세서
"""

import os
import glob
from pathlib import Path
from datetime import date
from decimal import Decimal
from typing import List, Dict, Any
import pytesseract
from PIL import Image
import re

from models import Receipt, ReceiptItem, ProcessingResult, ProcessingStatus
from excel_writer import export_manager, ExportRequest, ExportFormat
from final_main import extract_text_optimized, extract_date_from_text, smart_parse_receipt

class BatchReceiptProcessor:
    """여러 영수증을 배치로 처리하는 클래스"""

    def __init__(self, image_directory: str = "."):
        """
        Args:
            image_directory: 이미지가 있는 디렉토리 경로
        """
        self.image_directory = Path(image_directory)
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp'}
        self.results = []

    def find_receipt_images(self) -> List[Path]:
        """영수증 이미지 파일들을 찾기"""

        image_files = []
        for ext in self.supported_formats:
            pattern = str(self.image_directory / f"*{ext}")
            files = glob.glob(pattern, recursive=False)
            image_files.extend([Path(f) for f in files])

        # 대소문자 구분 없이 추가 검색
        for ext in ['.JPG', '.JPEG', '.PNG', '.TIFF', '.BMP']:
            pattern = str(self.image_directory / f"*{ext}")
            files = glob.glob(pattern, recursive=False)
            image_files.extend([Path(f) for f in files])

        # 중복 제거 및 정렬
        unique_files = list(set(image_files))
        unique_files.sort()

        print(f"🔍 발견된 이미지 파일: {len(unique_files)}개")
        for file in unique_files:
            print(f"   📸 {file.name}")

        return unique_files

    def process_single_image(self, image_path: Path) -> ProcessingResult:
        """단일 이미지 처리"""

        print(f"\n📸 처리 중: {image_path.name}")

        try:
            # OCR 텍스트 추출
            text = extract_text_optimized(str(image_path))

            if not text.strip():
                return ProcessingResult(
                    status=ProcessingStatus.FAILED,
                    error_message="OCR에서 텍스트를 추출할 수 없습니다",
                    source_file=image_path
                )

            # 날짜 추출
            receipt_date = extract_date_from_text(text)

            # 영수증 파싱
            items = smart_parse_receipt(text)

            if not items:
                return ProcessingResult(
                    status=ProcessingStatus.FAILED,
                    error_message="유효한 항목을 찾을 수 없습니다",
                    source_file=image_path,
                    extracted_text=text
                )

            # Receipt 객체 생성
            receipt = Receipt(
                date=receipt_date,
                items=items,
                source_file=image_path,
                extracted_text=text
            )

            total = sum(float(item.amount) for item in items)
            print(f"   ✅ 성공: {len(items)}개 항목, 총 ${total:.2f}")

            return ProcessingResult(
                status=ProcessingStatus.SUCCESS,
                receipt=receipt,
                source_file=image_path,
                extracted_text=text
            )

        except Exception as e:
            print(f"   ❌ 오류: {str(e)}")
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error_message=str(e),
                source_file=image_path
            )

    def process_all_images(self) -> Dict[str, Any]:
        """모든 이미지를 배치 처리"""

        print("🚀 배치 처리 시작")
        print("=" * 50)

        # 이미지 파일 찾기
        image_files = self.find_receipt_images()

        if not image_files:
            print("❌ 처리할 이미지가 없습니다.")
            return {"success": False, "message": "이미지가 없습니다"}

        # 각 이미지 처리
        successful_receipts = []
        failed_files = []

        for image_file in image_files:
            result = self.process_single_image(image_file)
            self.results.append(result)

            if result.status == ProcessingStatus.SUCCESS:
                successful_receipts.append(result.receipt)
            else:
                failed_files.append({
                    'file': image_file.name,
                    'error': result.error_message
                })

        # 결과 요약
        total_files = len(image_files)
        success_count = len(successful_receipts)
        failure_count = len(failed_files)

        print(f"\n📊 배치 처리 완료")
        print(f"   전체: {total_files}개")
        print(f"   성공: {success_count}개")
        print(f"   실패: {failure_count}개")

        if failed_files:
            print(f"\n❌ 실패한 파일들:")
            for failed in failed_files:
                print(f"   - {failed['file']}: {failed['error']}")

        # 성공한 영수증들의 총합 계산
        if successful_receipts:
            total_amount = sum(r.total_float for r in successful_receipts)
            total_items = sum(r.item_count for r in successful_receipts)

            print(f"\n💰 전체 요약:")
            print(f"   총 영수증: {len(successful_receipts)}개")
            print(f"   총 항목: {total_items}개")
            print(f"   총 금액: ${total_amount:.2f}")

            # Excel로 저장
            if successful_receipts:
                self.save_batch_results(successful_receipts)

        return {
            "success": True,
            "total_files": total_files,
            "successful": success_count,
            "failed": failure_count,
            "receipts": successful_receipts,
            "failed_files": failed_files
        }

    def save_batch_results(self, receipts: List[Receipt]) -> None:
        """배치 처리 결과를 Excel로 저장"""

        output_file = Path(f"batch_receipts_{date.today().strftime('%Y%m%d')}.xlsx")

        try:
            export_request = ExportRequest(
                format=ExportFormat.EXCEL,
                output_path=output_file,
                receipts=receipts,
                include_summary=True
            )

            export_manager.export_receipts(export_request)
            print(f"\n✅ 배치 결과 저장: {output_file}")
            print(f"   - 각 영수증별 시트")
            print(f"   - 요약 시트 포함")

        except Exception as e:
            print(f"❌ Excel 저장 실패: {e}")

    def interactive_mode(self) -> None:
        """대화형 모드로 실행"""

        print("🧾 영수증 배치 프로세서 v1.0")
        print("=" * 50)

        # 디렉토리 확인
        print(f"📁 검색 디렉토리: {self.image_directory.absolute()}")

        # 이미지 찾기
        images = self.find_receipt_images()

        if not images:
            print("\n❌ 이미지가 없습니다.")
            print("💡 다음을 확인해주세요:")
            print("   - 현재 폴더에 .jpg, .jpeg, .png 파일이 있는지")
            print("   - 파일 확장자가 올바른지")
            return

        print(f"\n계속 진행하시겠습니까? (y/n): ", end="")
        try:
            response = input().strip().lower()
            if response != 'y':
                print("취소되었습니다.")
                return
        except (EOFError, KeyboardInterrupt):
            print("\n취소되었습니다.")
            return

        # 배치 처리 실행
        self.process_all_images()

def main():
    """메인 실행 함수"""

    # 현재 디렉토리에서 실행
    processor = BatchReceiptProcessor(".")

    # 대화형 모드로 실행
    processor.interactive_mode()

def batch_process_directory(directory: str) -> Dict[str, Any]:
    """특정 디렉토리의 모든 영수증 처리 (API용)"""

    processor = BatchReceiptProcessor(directory)
    return processor.process_all_images()

if __name__ == "__main__":
    main()