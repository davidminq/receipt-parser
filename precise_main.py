#!/usr/bin/env python3
"""
정확한 금액 추출을 위한 개선된 프로그램
"""

import re
import datetime
import pytesseract
from PIL import Image
from decimal import Decimal
from models import Receipt, ReceiptItem
from excel_writer import export_manager, ExportRequest, ExportFormat
from pathlib import Path

def extract_text_optimized(image_path):
    """최적화된 OCR"""
    img = Image.open(image_path)
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

def smart_parse_receipt(text):
    """스마트한 영수증 파싱"""
    lines = text.split('\n')
    items = []
    seen_items = set()  # 중복 방지

    # 제외할 키워드
    exclude_keywords = [
        'total', 'subtotal', 'tax', 'change', 'tender', 'payment',
        'transaction', 'record', 'receipt', 'store', 'reg', 'cashier',
        'return', 'refund', 'balance', 'card', 'visa', 'amex', 'credit'
    ]

    print("=== 스마트 파싱 분석 ===")

    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line or len(line) < 5:
            continue

        # 금액 패턴 찾기
        amount_patterns = [
            r'(\d+\.\d{2})',    # 12.34
            r'(\d+,\d{2})',     # 12,34 (유럽식)
        ]

        amounts_found = []
        for pattern in amount_patterns:
            matches = re.findall(pattern, line)
            amounts_found.extend(matches)

        if not amounts_found:
            continue

        # 제외 키워드 체크
        line_lower = line.lower()
        should_exclude = any(keyword in line_lower for keyword in exclude_keywords)

        if should_exclude:
            print(f"{i:2d}: ❌ 제외 - {line}")
            print(f"    -> 제외 사유: 키워드 매칭")
            continue

        # 합리적인 금액만 선택
        valid_amounts = []
        for amount_str in amounts_found:
            try:
                amount_str = amount_str.replace(',', '.')
                amount = float(amount_str)
                if 0.50 <= amount <= 200.00:  # 더 좁은 범위 (일반적인 상품 가격)
                    valid_amounts.append(amount)
            except ValueError:
                continue

        if not valid_amounts:
            continue

        # 상품명 추출 (금액 제거)
        vendor_part = re.sub(r'\d+[\.,]\d+.*$', '', line).strip()
        vendor_part = re.sub(r'[^\w\s]', ' ', vendor_part)  # 특수문자 제거
        vendor_part = ' '.join(vendor_part.split())  # 공백 정리

        if len(vendor_part) < 3:  # 너무 짧은 상품명 제외
            continue

        # 중복 체크 (비슷한 상품명)
        vendor_key = vendor_part.lower()[:20]  # 첫 20자로 중복 체크
        if vendor_key in seen_items:
            print(f"{i:2d}: ❌ 중복 - {line}")
            print(f"    -> 중복 상품: {vendor_part}")
            continue

        seen_items.add(vendor_key)

        # 첫 번째 유효한 금액 사용
        amount = valid_amounts[0]
        vendor = vendor_part[:50]  # 최대 50자

        item = ReceiptItem(
            vendor=vendor,
            amount=Decimal(str(amount)),
            raw_text=line
        )
        items.append(item)

        print(f"{i:2d}: ✅ 추가 - {line}")
        print(f"    -> 상품: {vendor}")
        print(f"    -> 금액: ${amount}")

    return items

def main():
    # 이미지 경로
    image_path = "IMG_0140.jpeg"

    print(f"🔍 정밀 분석 중: {image_path}")
    print(f"🎯 목표 금액: $124.10")

    # OCR 텍스트 추출
    text = extract_text_optimized(image_path)
    print(f"✅ OCR 완료: {len(text)}자 추출")

    # 날짜 추출
    receipt_date = extract_date_from_text(text)
    print(f"📅 날짜: {receipt_date}")

    # 스마트 파싱
    items = smart_parse_receipt(text)

    if not items:
        print("❌ 유효한 항목을 찾을 수 없습니다.")
        return

    # Receipt 객체 생성
    receipt = Receipt(
        date=receipt_date,
        items=items,
        source_file=Path(image_path)
    )

    # 결과 출력
    print(f"\n🧾 최종 결과 ({len(items)}개 항목):")
    total = 0
    for item in items:
        print(f"- {item.vendor}: ${item.amount}")
        total += float(item.amount)

    print(f"\n💵 계산된 총합: ${total:.2f}")
    print(f"🎯 목표 금액: $124.10")
    print(f"📊 차이: ${abs(total - 124.10):.2f}")

    # Excel 저장
    export_request = ExportRequest(
        format=ExportFormat.EXCEL,
        output_path=Path("precise_receipts.xlsx"),
        receipts=[receipt]
    )

    export_manager.export_receipts(export_request)
    print("✅ Precise Excel 저장 완료: precise_receipts.xlsx")

if __name__ == "__main__":
    main()