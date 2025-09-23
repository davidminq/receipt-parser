#!/usr/bin/env python3
"""
Google Vision API 무료 버전 (월 1000건 무료)
"""

import base64
import requests
import json
from pathlib import Path
from decimal import Decimal
from models import Receipt, ReceiptItem
from excel_writer import export_manager, ExportRequest, ExportFormat
import datetime
import re

class GoogleVisionParser:
    """Google Vision API를 사용한 무료 영수증 파서"""

    def __init__(self, api_key: str = None):
        """
        Google Cloud API 키 설정
        무료 계정: https://cloud.google.com/vision/docs/quickstart
        """
        self.api_key = api_key
        self.base_url = "https://vision.googleapis.com/v1/images:annotate"

    def encode_image(self, image_path: str) -> str:
        """이미지를 base64로 인코딩"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def extract_text_google(self, image_path: str) -> str:
        """Google Vision API로 텍스트 추출"""

        if not self.api_key:
            print("❌ Google Cloud API 키가 필요합니다.")
            print("🔗 무료 계정 생성: https://cloud.google.com/vision/docs/quickstart")
            return ""

        base64_image = self.encode_image(image_path)

        payload = {
            "requests": [
                {
                    "image": {
                        "content": base64_image
                    },
                    "features": [
                        {
                            "type": "TEXT_DETECTION",
                            "maxResults": 1
                        }
                    ]
                }
            ]
        }

        try:
            response = requests.post(
                f"{self.base_url}?key={self.api_key}",
                headers={'Content-Type': 'application/json'},
                data=json.dumps(payload)
            )

            if response.status_code == 200:
                result = response.json()
                if 'responses' in result and result['responses']:
                    annotations = result['responses'][0].get('textAnnotations', [])
                    if annotations:
                        return annotations[0]['description']

            print(f"❌ Google Vision API 오류: {response.status_code}")
            return ""

        except Exception as e:
            print(f"❌ API 호출 오류: {e}")
            return ""

def demo_without_api():
    """API 없이 데모 실행"""

    print("=== Google Vision API 무료 데모 ===")
    print()
    print("🔧 설정 방법:")
    print("1. https://cloud.google.com/vision/docs/quickstart 방문")
    print("2. 무료 Google Cloud 계정 생성")
    print("3. Vision API 활성화 (월 1000건 무료)")
    print("4. API 키 생성")
    print()
    print("💡 무료 할당량:")
    print("- TEXT_DETECTION: 월 1000건 무료")
    print("- 그 이후: $1.50/1000건")
    print()

    # 시뮬레이션된 결과 (실제 Google Vision 결과처럼)
    simulated_result = """
    IKEA
    Receipt

    MOSSLANDA Picture ledge    $12.99    $9.99  (15% off)
    MOSSLANDA Picture ledge    $12.99    $9.99  (15% off)
    MOSSLANDA Picture ledge    $12.99    $9.99  (15% off)
    RIBBA Frame                $15.99    $13.59 (15% off)
    RIBBA Frame                $15.99    $13.59 (15% off)
    HEMNES Bookshelf          $89.99    $76.49 (15% off)

    Subtotal:                            $122.64
    Tax (8.875%):                         $10.88
    Total:                               $133.52
    """

    print("🔍 시뮬레이션된 Google Vision 결과:")
    print(simulated_result)

    # 스마트 파싱 (할인된 가격만 추출)
    lines = simulated_result.strip().split('\n')
    items = []

    for line in lines:
        line = line.strip()
        if not line or 'IKEA' in line or 'Receipt' in line or 'Subtotal' in line or 'Tax' in line or 'Total' in line:
            continue

        # 할인된 가격 패턴 찾기: $9.99 (15% off)
        discount_pattern = r'\$(\d+\.\d{2})\s*\(\d+%\s*off\)'
        matches = re.findall(discount_pattern, line)

        if matches:
            # 상품명 추출
            vendor = re.sub(r'\$.*', '', line).strip()
            vendor = re.sub(r'\s+', ' ', vendor)

            # 할인된 가격
            price = float(matches[0])

            item = ReceiptItem(
                vendor=vendor,
                amount=Decimal(str(price))
            )
            items.append(item)

    # 결과 출력
    print(f"\n🧾 추출된 항목들 ({len(items)}개):")
    total = 0
    for item in items:
        print(f"- {item.vendor}: ${item.amount}")
        total += float(item.amount)

    print(f"\n💵 할인 적용 총합: ${total:.2f}")
    print("✅ 실제 Google Vision API를 사용하면 더 정확한 결과를 얻을 수 있습니다!")

    return items

if __name__ == "__main__":
    print("Google Vision API 키가 있으신가요? (y/n)")
    has_api = input().strip().lower()

    if has_api == 'y':
        api_key = input("API 키를 입력하세요: ").strip()
        parser = GoogleVisionParser(api_key)
        text = parser.extract_text_google("IMG_0140.jpeg")
        print("추출된 텍스트:")
        print(text)
    else:
        print("데모 모드로 실행합니다...")
        demo_without_api()