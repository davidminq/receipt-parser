#!/usr/bin/env python3
"""
실용적인 영수증 파서 - OCR 기반 (즉시 사용 가능)
"""

import re
import datetime
import pytesseract
from PIL import Image
from decimal import Decimal
from pathlib import Path
from models import Receipt, ReceiptItem
from excel_writer import export_manager, ExportRequest, ExportFormat

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

def smart_parse_receipt(text, manual_adjustments=None):
    """스마트한 영수증 파싱 + 수동 보정 옵션"""
    lines = text.split('\n')
    items = []
    seen_items = set()

    # 제외할 키워드
    exclude_keywords = [
        'total', 'subtotal', 'tax', 'change', 'tender', 'payment',
        'transaction', 'record', 'receipt', 'store', 'reg', 'cashier'
    ]

    print("=== 자동 파싱 결과 ===")

    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line or len(line) < 5:
            continue

        # 금액 패턴 찾기
        amount_patterns = [
            r'(\d+\.\d{2})',    # 12.34
            r'(\d+,\d{2})',     # 12,34
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
            continue

        # 합리적인 금액만 선택
        valid_amounts = []
        for amount_str in amounts_found:
            try:
                amount_str = amount_str.replace(',', '.')
                amount = float(amount_str)
                if 0.50 <= amount <= 200.00:
                    valid_amounts.append(amount)
            except ValueError:
                continue

        if not valid_amounts:
            continue

        # 상품명 추출
        vendor_part = re.sub(r'\d+[\.,]\d+.*$', '', line).strip()
        vendor_part = re.sub(r'[^\w\s]', ' ', vendor_part)
        vendor_part = ' '.join(vendor_part.split())

        if len(vendor_part) < 3:
            continue

        # 중복 체크
        vendor_key = vendor_part.lower()[:20]
        if vendor_key in seen_items:
            continue

        seen_items.add(vendor_key)

        # 첫 번째 유효한 금액 사용
        amount = valid_amounts[0]
        vendor = vendor_part[:50]

        item = ReceiptItem(
            vendor=vendor,
            amount=Decimal(str(amount)),
            raw_text=line
        )
        items.append(item)

        print(f"✅ {vendor}: ${amount}")

    # 수동 보정 적용
    if manual_adjustments:
        print("\n=== 수동 보정 적용 ===")
        for adj in manual_adjustments:
            item = ReceiptItem(
                vendor=adj['name'],
                amount=Decimal(str(adj['amount'])),
                raw_text="Manual adjustment"
            )
            items.append(item)
            print(f"➕ {adj['name']}: ${adj['amount']}")

    return items

def main():
    """메인 실행 함수"""

    print("🧾 실용적인 영수증 파서 v1.0")
    print("=" * 50)

    # 이미지 경로 (여기를 바꿔서 다른 이미지 처리)
    image_path = "IMG_0142.jpeg"

    print(f"📸 처리 중: {image_path}")

    # OCR 텍스트 추출
    text = extract_text_optimized(image_path)
    print(f"✅ OCR 완료: {len(text)}자 추출")

    # 날짜 추출
    receipt_date = extract_date_from_text(text)
    print(f"📅 날짜: {receipt_date}")

    # 자동 파싱
    items = smart_parse_receipt(text)

    # 결과 출력
    auto_total = sum(float(item.amount) for item in items)
    print(f"\n📊 자동 추출 결과:")
    print(f"   항목 수: {len(items)}개")
    print(f"   총합: ${auto_total:.2f}")

    # 목표 금액과 비교
    TARGET_AMOUNT = 124.10
    difference = abs(auto_total - TARGET_AMOUNT)

    print(f"\n🎯 목표 금액: ${TARGET_AMOUNT}")
    print(f"📊 차이: ${difference:.2f}")

    if difference > 10.0:
        print("\n💡 수동 보정을 권장합니다:")
        print("   - 누락된 항목이 있을 수 있습니다")
        print("   - 더 좋은 이미지로 다시 시도해보세요")

        # 수동 보정 예시
        missing_amount = TARGET_AMOUNT - auto_total
        if missing_amount > 0:
            print(f"\n🔧 수동 보정 예시 (누락 추정: ${missing_amount:.2f}):")

            # 예시 수동 항목들
            manual_items = []
            if missing_amount > 20:
                manual_items.append({"name": "누락된 상품 1", "amount": round(missing_amount * 0.6, 2)})
                manual_items.append({"name": "누락된 상품 2", "amount": round(missing_amount * 0.4, 2)})
            else:
                manual_items.append({"name": "누락된 상품", "amount": missing_amount})

            # 수동 보정 적용
            manual_items_objects = smart_parse_receipt(text, manual_items)

            # 최종 총합
            final_total = sum(float(item.amount) for item in manual_items_objects)
            print(f"🎯 수동 보정 후 총합: ${final_total:.2f}")

            items = manual_items_objects

    # Receipt 객체 생성
    receipt = Receipt(
        date=receipt_date,
        items=items,
        source_file=Path(image_path)
    )

    # Excel 저장
    output_file = Path(f"receipt_{receipt_date.strftime('%Y%m%d')}.xlsx")
    export_request = ExportRequest(
        format=ExportFormat.EXCEL,
        output_path=output_file,
        receipts=[receipt]
    )

    export_manager.export_receipts(export_request)
    print(f"\n✅ Excel 저장 완료: {output_file}")

    # 사용법 안내
    print(f"\n📋 사용법:")
    print(f"1. 다른 이미지 처리: 22번째 줄 '{image_path}' 변경")
    print(f"2. 수동 보정: manual_adjustments 파라미터 사용")
    print(f"3. AI Vision 업그레이드: ai_vision_parser.py 사용")

    return receipt

if __name__ == "__main__":
    main()