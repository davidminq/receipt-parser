#!/usr/bin/env python3
"""
숫자 인식에 특화된 OCR 설정
"""

import pytesseract
from PIL import Image
import re

def extract_with_number_focus(image_path: str):
    """숫자 인식에 특화된 OCR"""

    img = Image.open(image_path)

    # 다양한 OCR 설정 시도
    configs = [
        # 1. 숫자만 인식하도록 제한
        {
            'config': '--psm 6 -c tessedit_char_whitelist=0123456789.,$',
            'name': '숫자만'
        },
        # 2. 숫자 + 기본 문자
        {
            'config': '--psm 6 -c tessedit_char_whitelist=0123456789.,$ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ',
            'name': '숫자+문자'
        },
        # 3. PSM 8 (단일 단어)
        {
            'config': '--psm 8',
            'name': 'PSM 8'
        },
        # 4. PSM 7 (단일 줄)
        {
            'config': '--psm 7',
            'name': 'PSM 7'
        },
        # 5. digits 모드
        {
            'config': '--psm 6 digits',
            'name': 'digits 모드'
        }
    ]

    results = {}

    for config in configs:
        try:
            text = pytesseract.image_to_string(img, config=config['config'])
            results[config['name']] = text

            print(f"\n=== {config['name']} ===")
            lines = [line.strip() for line in text.split('\n') if line.strip()]

            # 금액 패턴 찾기
            amounts = []
            for line in lines:
                # 금액 패턴들
                patterns = [
                    r'\$?\s*(\d+\.\d{2})',
                    r'\$?\s*(\d+,\d{3}\.\d{2})',
                    r'(\d+\.\d{2})',
                    r'(\d+,\d{2})',
                    r'(\d+\.\d{1})',
                ]

                for pattern in patterns:
                    matches = re.findall(pattern, line)
                    amounts.extend(matches)

            if amounts:
                print(f"발견된 금액들: {amounts}")

            # 처음 10줄만 출력
            for i, line in enumerate(lines[:10], 1):
                print(f"{i:2d}: {line}")

        except Exception as e:
            print(f"{config['name']} 오류: {e}")

    return results

if __name__ == "__main__":
    results = extract_with_number_focus("IMG_0140.jpeg")