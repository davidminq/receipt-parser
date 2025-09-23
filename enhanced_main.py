#!/usr/bin/env python3
"""
숫자 인식이 개선된 메인 프로그램
"""

import re
import datetime
import pytesseract
from PIL import Image
from decimal import Decimal
from models import Receipt, ReceiptItem
from excel_writer import export_manager, ExportRequest, ExportFormat
from pathlib import Path

def extract_text_with_number_focus(image_path):
    """숫자 인식에 특화된 OCR"""
    img = Image.open(image_path)

    # 숫자 + 기본 문자로 인식
    config = '--psm 6 -c tessedit_char_whitelist=0123456789.,$ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz '
    text = pytesseract.image_to_string(img, config=config)

    return text

def extract_date_from_text(text):
    """텍스트에서 날짜 추출"""
    match = re.search(r"(\d{4}[-/]\d{2}[-/]\d{2})|(\d{2}[-/]\d{2}[-/]\d{4})", text)
    if match:
        date_str = match.group()
        try:
            if '-' in date_str:
                return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            else:
                return datetime.datetime.strptime(date_str, "%m/%d/%Y").date()
        except ValueError:
            pass
    return datetime.date.today()

def parse_receipt_enhanced(text):
    """개선된 영수증 파싱"""
    lines = text.split('\n')
    items = []

    print("=== 라인별 분석 ===")

    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue

        # 금액 패턴들
        amount_patterns = [
            r'(\d+\.\d{2})',    # 12.34
            r'(\d+,\d{2})',     # 12,34 (유럽식)
            r'(\d+\.\d{1})',    # 12.3
        ]

        amounts_found = []
        for pattern in amount_patterns:
            matches = re.findall(pattern, line)
            amounts_found.extend(matches)

        if amounts_found:
            print(f"{i:2d}: {line}")
            print(f"    -> 금액 발견: {amounts_found}")

            # 가장 합리적인 금액 선택 (0.01 ~ 1000.00 범위)
            for amount_str in amounts_found:
                try:
                    # 쉼표를 점으로 변환 (유럽식 -> 미국식)
                    amount_str = amount_str.replace(',', '.')
                    amount = float(amount_str)

                    if 0.01 <= amount <= 1000.00:  # 합리적인 범위
                        # 상품명 추출 (금액 앞의 텍스트)
                        vendor_part = re.sub(r'\d+[\.,]\d+.*$', '', line).strip()
                        if len(vendor_part) > 2:  # 의미있는 상품명
                            vendor = vendor_part[:50]  # 최대 50자

                            item = ReceiptItem(
                                vendor=vendor,
                                amount=Decimal(str(amount)),
                                raw_text=line
                            )
                            items.append(item)
                            print(f"    -> 추가됨: {vendor} = ${amount}")
                            break  # 첫 번째 유효한 금액만 사용

                except ValueError:
                    continue

    return items

def main():
    # 이미지 경로 설정
    image_path = "IMG_0140.jpeg"

    print(f"🔍 이미지 분석 중: {image_path}")

    # OCR로 텍스트 추출
    text = extract_text_with_number_focus(image_path)
    print(f"✅ OCR 완료: {len(text)}자 추출")

    # 날짜 추출
    receipt_date = extract_date_from_text(text)
    print(f"📅 날짜: {receipt_date}")

    # 개선된 파싱
    items = parse_receipt_enhanced(text)

    if not items:
        print("❌ 항목을 찾을 수 없습니다.")
        return

    # Receipt 객체 생성
    receipt = Receipt(
        date=receipt_date,
        items=items,
        source_file=Path(image_path)
    )

    # 결과 출력
    print("\n🧾 최종 추출 결과:")
    total = 0
    for item in items:
        print(f"- {item.vendor}: ${item.amount}")
        total += float(item.amount)

    print(f"\n💵 총합: ${total:.2f}")

    # Excel 저장
    export_request = ExportRequest(
        format=ExportFormat.EXCEL,
        output_path=Path("enhanced_receipts.xlsx"),
        receipts=[receipt]
    )

    export_manager.export_receipts(export_request)
    print("✅ Enhanced Excel 저장 완료: enhanced_receipts.xlsx")

if __name__ == "__main__":
    main()