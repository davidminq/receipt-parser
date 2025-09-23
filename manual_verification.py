#!/usr/bin/env python3
"""
수동 검증 및 목표 금액 달성을 위한 스크립트
"""

# 실제 영수증에서 보이는 것 (사용자가 확인한 값들)
ACTUAL_RECEIPT_ITEMS = [
    # 사용자가 실제로 확인한 금액들
    # 예: ("MOSSLANDA", 9.99),
    # 이 부분을 실제 영수증 내용으로 채워주세요
]

TARGET_TOTAL = 124.10

def analyze_discrepancy():
    """현재 추출된 값과 실제 값의 차이 분석"""

    # 현재 OCR로 찾은 값들
    ocr_items = [
        ("MOSSLANDA (item 1)", 9.99),
        ("MOSSLANDA (item 2)", 9.99),
        ("MOSSLANDA (item 3)", 9.99),
        ("Other item", 42.61),
    ]

    ocr_total = sum(item[1] for item in ocr_items)

    print("=== 현재 상황 분석 ===")
    print(f"OCR로 찾은 총합: ${ocr_total:.2f}")
    print(f"실제 목표 총합: ${TARGET_TOTAL:.2f}")
    print(f"누락된 금액: ${TARGET_TOTAL - ocr_total:.2f}")

    print(f"\n현재 찾은 항목들:")
    for item, amount in ocr_items:
        print(f"  - {item}: ${amount:.2f}")

    # 누락 분석
    missing_amount = TARGET_TOTAL - ocr_total
    print(f"\n=== 누락 분석 ===")
    print(f"누락된 ${missing_amount:.2f}는 다음일 수 있습니다:")
    print(f"  - 세금 (tax): 보통 5-10%")
    print(f"  - 추가 상품들")
    print(f"  - OCR이 인식하지 못한 항목들")

    # 세금 계산
    subtotal = ocr_total
    tax_rate_estimates = [0.05, 0.075, 0.10, 0.125]

    print(f"\n세금 가능성 분석:")
    for rate in tax_rate_estimates:
        tax = subtotal * rate
        total_with_tax = subtotal + tax
        print(f"  - {rate*100:4.1f}% 세금: ${tax:.2f} (총합: ${total_with_tax:.2f})")

def suggest_improvements():
    """개선 방안 제안"""

    print("\n=== 개선 방안 ===")
    print("1. 이미지 품질:")
    print("   - 더 밝은 조명에서 재촬영")
    print("   - 영수증을 평평하게 펴서 촬영")
    print("   - 스마트폰 스캔 앱 사용")

    print("\n2. OCR 설정 개선:")
    print("   - 더 많은 PSM 모드 시도")
    print("   - 언어 설정 변경")
    print("   - 이미지 전처리 강화")

    print("\n3. 수동 보정:")
    print("   - OCR 결과를 수동으로 확인/수정")
    print("   - 놓친 항목을 수동으로 추가")

def create_corrected_receipt():
    """수정된 영수증 생성 (예시)"""

    # 실제 영수증 내용을 기반으로 한 예시
    corrected_items = [
        ("MOSSLANDA Picture ledge", 9.99),
        ("MOSSLANDA Picture ledge", 9.99),
        ("MOSSLANDA Picture ledge", 9.99),
        ("Additional item 1", 15.00),  # 가상의 누락 항목
        ("Additional item 2", 25.00),  # 가상의 누락 항목
        ("Additional item 3", 35.00),  # 가상의 누락 항목
    ]

    subtotal = sum(item[1] for item in corrected_items)
    tax = round(subtotal * 0.08875, 2)  # 8.875% 세금 (NYC 예시)
    total = subtotal + tax

    print(f"\n=== 수정된 영수증 (예시) ===")
    for item, amount in corrected_items:
        print(f"  {item}: ${amount:.2f}")

    print(f"\n  소계: ${subtotal:.2f}")
    print(f"  세금: ${tax:.2f}")
    print(f"  총합: ${total:.2f}")

    if abs(total - TARGET_TOTAL) < 0.50:
        print(f"✅ 목표 금액과 거의 일치!")
    else:
        print(f"❌ 목표와 차이: ${abs(total - TARGET_TOTAL):.2f}")

if __name__ == "__main__":
    analyze_discrepancy()
    suggest_improvements()
    create_corrected_receipt()

    print(f"\n=== 결론 ===")
    print("현재 OCR로는 완벽한 추출이 어려운 상황입니다.")
    print("다음 중 하나를 선택하세요:")
    print("1. 더 좋은 품질의 영수증 이미지로 다시 시도")
    print("2. OCR 결과를 수동으로 보정")
    print("3. 스마트폰 영수증 스캔 앱 사용")