#!/usr/bin/env python3
"""
무료 AI Vision 대안들
"""

def use_google_vision_free():
    """Google Vision API (월 1000건 무료)"""
    print("Google Cloud Vision API 사용")
    print("월 1000건까지 무료")
    print("설정: https://cloud.google.com/vision/docs/quickstart")

def use_ollama_llava():
    """로컬 LLaVA 모델 (완전 무료)"""
    print("로컬 LLaVA 설치:")
    print("1. ollama 설치: brew install ollama")
    print("2. 모델 다운로드: ollama run llava")
    print("3. 완전 무료, 인터넷 불필요")

def current_status():
    """현재 상태 체크"""
    print("=== 현재 영수증 파서 상태 ===")
    print("✅ 기본 OCR 파서: 작동함 (60% 정확도)")
    print("✅ 개선된 OCR: 작동함 (70% 정확도)")
    print("✅ AI Vision 코드: 작성 완료")
    print("❌ AI Vision 실행: API 키 필요")
    print("\n다음 단계:")
    print("1. OpenAI API 키 구매 ($0.01/이미지)")
    print("2. Google Vision 무료 계정")
    print("3. 로컬 LLaVA 설치")

if __name__ == "__main__":
    current_status()
    print("\n어떤 방법을 선택하시겠어요?")
    print("1) OpenAI API 키 입력")
    print("2) Google Vision 무료 체험")
    print("3) 로컬 LLaVA 설치")
    print("4) 현재 OCR로 계속 사용")