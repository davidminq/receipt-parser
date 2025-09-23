#!/usr/bin/env python3
"""
OCR 설정을 다양하게 테스트해보는 스크립트
"""

from ocr_parser import TesseractOCR
from pathlib import Path

def test_different_ocr_settings(image_path: str):
    """다양한 OCR 설정으로 테스트"""

    print(f"=== OCR 테스트: {image_path} ===\n")

    # 다양한 PSM 모드 테스트
    psm_modes = [6, 7, 8, 11, 12, 13]

    for psm in psm_modes:
        print(f"--- PSM 모드 {psm} ---")
        try:
            ocr = TesseractOCR()
            text = ocr.extract_text(Path(image_path), psm_mode=psm)

            # 첫 10줄만 보여주기
            lines = text.split('\n')[:10]
            for i, line in enumerate(lines, 1):
                if line.strip():
                    print(f"{i:2d}: {line}")
            print()

        except Exception as e:
            print(f"오류: {e}\n")

if __name__ == "__main__":
    test_different_ocr_settings("IMG_0140.jpeg")