#!/usr/bin/env python3
"""
OCR + AI Vision 하이브리드 파서
"""

def hybrid_receipt_parser(image_path: str):
    """
    1단계: OCR로 빠른 추출 시도
    2단계: 결과가 부정확하면 AI Vision 사용
    """

    # 1단계: OCR 시도
    ocr_result = extract_with_ocr(image_path)

    # 정확도 체크
    if is_result_reliable(ocr_result):
        print("✅ OCR 결과 신뢰성 높음")
        return ocr_result
    else:
        print("⚠️ OCR 결과 신뢰성 낮음 -> AI Vision 사용")
        return extract_with_ai_vision(image_path)

def is_result_reliable(result) -> bool:
    """OCR 결과 신뢰성 판단"""
    # 항목 수가 너무 적거나
    # 금액이 비현실적이거나
    # 패턴이 이상하면 False
    return len(result.items) >= 3 and result.total_float < 1000

# 비용 효율적이고 정확한 최고의 조합! 💡