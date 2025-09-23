#!/usr/bin/env python3
"""
최고 품질의 OCR을 위한 강화된 전처리
"""

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import numpy as np
import cv2

def ultimate_preprocess(image_path):
    """최고 품질의 이미지 전처리"""

    # PIL로 기본 로드
    img = Image.open(image_path)
    print(f"원본: {img.size}, {img.mode}")

    # OpenCV로 변환 (더 정교한 처리를 위해)
    img_cv = cv2.imread(image_path)
    if img_cv is None:
        print("OpenCV 로드 실패, PIL 사용")
        return preprocess_with_pil(image_path)

    # 그레이스케일 변환
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    # 1. 노이즈 제거
    denoised = cv2.fastNlMeansDenoising(gray)

    # 2. 대비 개선 (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    enhanced = clahe.apply(denoised)

    # 3. 적응형 이진화
    binary = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    # 4. 모폴로지 연산 (텍스트 연결)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
    processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    # 5. 크기 확대 (OCR 정확도 향상)
    height, width = processed.shape
    scale_factor = max(2000 / width, 2000 / height)
    if scale_factor > 1:
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        processed = cv2.resize(processed, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

    # PIL로 다시 변환
    result_img = Image.fromarray(processed)

    # 저장
    output_path = f"ultimate_{image_path}"
    result_img.save(output_path)
    print(f"✅ 최고 품질 전처리 완료: {output_path}")

    return output_path

def preprocess_with_pil(image_path):
    """PIL 기반 백업 전처리"""
    img = Image.open(image_path)

    # 그레이스케일
    if img.mode != 'L':
        img = img.convert('L')

    # 강한 대비
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(3.0)

    # 밝기
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.3)

    # 선명도
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(3.0)

    # 크기 확대
    width, height = img.size
    if width < 2000:
        scale = 2000 / width
        new_size = (int(width * scale), int(height * scale))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    # 저장
    output_path = f"pil_processed_{image_path}"
    img.save(output_path)
    return output_path

def test_multiple_ocr_methods(image_path):
    """여러 OCR 방법으로 테스트"""

    configs = [
        ('기본 PSM6', '--psm 6'),
        ('PSM4 컬럼', '--psm 4'),
        ('PSM3 완전자동', '--psm 3'),
        ('숫자특화', '--psm 6 -c tessedit_char_whitelist=0123456789.,$ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz '),
        ('OEM0', '--psm 6 --oem 0'),
        ('OEM1', '--psm 6 --oem 1'),
    ]

    img = Image.open(image_path)

    all_amounts = set()

    for name, config in configs:
        print(f'\n=== {name} ===')
        try:
            text = pytesseract.image_to_string(img, config=config)

            # 금액 찾기
            import re
            amounts = re.findall(r'\d+[\.,]\d{1,2}', text)
            print(f'발견된 금액: {amounts}')
            all_amounts.update(amounts)

            # 유의미한 라인들
            lines = [line.strip() for line in text.split('\n') if line.strip() and len(line.strip()) > 5]
            print(f'의미있는 라인 수: {len(lines)}')

        except Exception as e:
            print(f'오류: {e}')

    print(f'\n=== 전체 발견된 금액들 ===')
    print(sorted(all_amounts))

if __name__ == "__main__":
    # 최고 품질 전처리
    processed_path = ultimate_preprocess("IMG_0140.jpeg")

    print('\n' + '='*60)
    print('원본 이미지 테스트')
    print('='*60)
    test_multiple_ocr_methods("IMG_0140.jpeg")

    print('\n' + '='*60)
    print('전처리된 이미지 테스트')
    print('='*60)
    test_multiple_ocr_methods(processed_path)