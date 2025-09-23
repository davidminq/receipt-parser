#!/usr/bin/env python3
"""
OCR 결과를 상세히 분석하는 디버그 스크립트
"""

import pytesseract
from PIL import Image
import re

def detailed_analysis(image_path):
    """상세한 OCR 분석"""

    img = Image.open(image_path)

    # 여러 설정으로 텍스트 추출
    configs = [
        '--psm 6',  # 기본
        '--psm 4',  # 단일 컬럼
        '--psm 6 -c tessedit_char_whitelist=0123456789.,$ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ',
    ]

    for i, config in enumerate(configs):
        print(f"\n{'='*60}")
        print(f"설정 {i+1}: {config}")
        print('='*60)

        text = pytesseract.image_to_string(img, config=config)
        lines = text.split('\n')

        # 금액 패턴 찾기
        amount_lines = []
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            # 다양한 금액 패턴
            patterns = [
                r'\$\s*(\d+\.\d{2})',     # $12.34
                r'(\d+\.\d{2})',          # 12.34
                r'(\d+,\d{2})',           # 12,34
                r'(\d+\.\d{1})',          # 12.3
                r'-(\d+\.\d{2})',         # -12.34
                r'(\d+\.\d{2})\s*USD',    # 12.34 USD
            ]

            amounts_in_line = []
            for pattern in patterns:
                matches = re.findall(pattern, line)
                amounts_in_line.extend(matches)

            if amounts_in_line:
                # 숫자를 float로 변환해서 합리적인 범위인지 체크
                valid_amounts = []
                for amt_str in amounts_in_line:
                    try:
                        amt_str = amt_str.replace(',', '.')
                        amt = float(amt_str)
                        if 0.01 <= amt <= 500.00:  # 영수증 금액 범위
                            valid_amounts.append(amt)
                    except:
                        pass

                if valid_amounts:
                    amount_lines.append({
                        'line_num': line_num,
                        'text': line,
                        'amounts': valid_amounts
                    })

        # 결과 출력
        print(f"발견된 금액 라인들 (총 {len(amount_lines)}개):")
        total = 0
        for item in amount_lines:
            print(f"{item['line_num']:3d}: {item['text']}")
            print(f"     금액: {item['amounts']}")
            if item['amounts']:
                total += max(item['amounts'])  # 가장 큰 금액 선택

        print(f"\n예상 총합: ${total:.2f}")

        # 전체 텍스트에서 모든 숫자 패턴 찾기
        all_numbers = re.findall(r'\d+\.\d{2}', text)
        print(f"\n모든 xx.xx 패턴: {all_numbers}")

if __name__ == "__main__":
    detailed_analysis("IMG_0140.jpeg")