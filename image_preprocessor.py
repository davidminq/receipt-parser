#!/usr/bin/env python3
"""
이미지 전처리를 통한 OCR 품질 개선
"""

from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
from pathlib import Path

def preprocess_receipt_image(image_path: str, output_path: str = None):
    """영수증 이미지 전처리"""

    if output_path is None:
        output_path = f"processed_{Path(image_path).name}"

    # 이미지 열기
    img = Image.open(image_path)
    print(f"원본 이미지 크기: {img.size}")
    print(f"원본 이미지 모드: {img.mode}")

    # 1. 그레이스케일 변환
    if img.mode != 'L':
        img = img.convert('L')
        print("✓ 그레이스케일 변환")

    # 2. 대비 증가
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    print("✓ 대비 증가")

    # 3. 밝기 조정
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.2)
    print("✓ 밝기 조정")

    # 4. 선명도 증가
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(2.0)
    print("✓ 선명도 증가")

    # 5. 크기 조정 (OCR 성능 향상을 위해)
    width, height = img.size
    if width < 1000:
        scale_factor = 1000 / width
        new_size = (int(width * scale_factor), int(height * scale_factor))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        print(f"✓ 크기 조정: {new_size}")

    # 6. 노이즈 제거
    img = img.filter(ImageFilter.MedianFilter(size=3))
    print("✓ 노이즈 제거")

    # 저장
    img.save(output_path)
    print(f"✓ 전처리된 이미지 저장: {output_path}")

    return output_path

if __name__ == "__main__":
    # 테스트
    processed_path = preprocess_receipt_image("IMG_0140.jpeg")

    # OCR 테스트
    from ocr_parser import ocr_manager

    print("\n=== 전처리된 이미지 OCR 테스트 ===")
    text = ocr_manager.extract_text_from_image(processed_path)

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    print(f"추출된 줄 수: {len(lines)}")

    # 처음 20줄 출력
    for i, line in enumerate(lines[:20], 1):
        print(f"{i:2d}: {line}")