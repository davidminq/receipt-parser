#!/usr/bin/env python3
"""
AI Vision API를 사용한 지능형 영수증 파서
"""

import openai
import base64
from pathlib import Path
from decimal import Decimal
from models import Receipt, ReceiptItem
from excel_writer import export_manager, ExportRequest, ExportFormat
import datetime
import json

class AIVisionReceiptParser:
    """AI Vision을 사용한 영수증 파서"""

    def __init__(self, api_key: str):
        """
        Args:
            api_key: OpenAI API 키
        """
        self.client = openai.OpenAI(api_key=api_key)

    def encode_image(self, image_path: str) -> str:
        """이미지를 base64로 인코딩"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def parse_receipt_with_ai(self, image_path: str) -> Receipt:
        """AI Vision으로 영수증 파싱"""

        base64_image = self.encode_image(image_path)

        prompt = """
        이 영수증 이미지를 분석해서 다음 정보를 JSON 형태로 추출해주세요:

        1. 각 상품의 이름과 최종 결제 금액 (할인이 적용된 실제 금액)
        2. 총 결제 금액
        3. 날짜 (있다면)

        JSON 형식:
        {
            "items": [
                {
                    "name": "상품명",
                    "price": 9.99
                }
            ],
            "total": 124.10,
            "date": "2025-09-23"
        }

        주의사항:
        - 할인이 적용된 최종 가격만 포함
        - 세금, 팁 등은 별도로 명시
        - 중복 항목 제거
        - 실제로 지불한 금액만 계산

        영수증을 자세히 분석해서 정확한 JSON을 만들어주세요.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )

            # AI 응답에서 JSON 추출
            ai_response = response.choices[0].message.content
            print("=== AI 분석 결과 ===")
            print(ai_response)

            # JSON 파싱
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            json_str = ai_response[json_start:json_end]

            receipt_data = json.loads(json_str)

            # Receipt 객체 생성
            items = []
            for item_data in receipt_data.get('items', []):
                item = ReceiptItem(
                    vendor=item_data['name'],
                    amount=Decimal(str(item_data['price']))
                )
                items.append(item)

            # 날짜 처리
            date_str = receipt_data.get('date')
            if date_str:
                try:
                    receipt_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                except:
                    receipt_date = datetime.date.today()
            else:
                receipt_date = datetime.date.today()

            receipt = Receipt(
                date=receipt_date,
                items=items,
                source_file=Path(image_path)
            )

            return receipt

        except Exception as e:
            print(f"AI 파싱 오류: {e}")
            raise

def main():
    """메인 실행 함수"""

    # OpenAI API 키 설정 (환경변수 또는 직접 입력)
    import os
    api_key = os.getenv('OPENAI_API_KEY')

    if not api_key:
        print("❌ OPENAI_API_KEY 환경변수를 설정해주세요.")
        print("또는 직접 입력:")
        api_key = input("OpenAI API 키: ").strip()

    if not api_key:
        print("❌ API 키가 필요합니다.")
        return

    # 이미지 경로
    image_path = "IMG_0140.jpeg"

    print(f"🤖 AI Vision으로 분석 중: {image_path}")
    print(f"🎯 목표 금액: $124.10")

    try:
        # AI 파서 초기화
        parser = AIVisionReceiptParser(api_key)

        # AI로 영수증 분석
        receipt = parser.parse_receipt_with_ai(image_path)

        # 결과 출력
        print(f"\n🧾 AI 추출 결과 ({len(receipt.items)}개 항목):")
        total = 0
        for item in receipt.items:
            print(f"- {item.vendor}: ${item.amount}")
            total += float(item.amount)

        print(f"\n💵 AI 계산 총합: ${total:.2f}")
        print(f"🎯 목표 금액: $124.10")
        print(f"📊 차이: ${abs(total - 124.10):.2f}")

        if abs(total - 124.10) < 1.0:
            print("✅ 목표 금액과 거의 일치!")
        else:
            print("⚠️  차이가 있습니다.")

        # Excel 저장
        export_request = ExportRequest(
            format=ExportFormat.EXCEL,
            output_path=Path("ai_vision_receipts.xlsx"),
            receipts=[receipt]
        )

        export_manager.export_receipts(export_request)
        print("✅ AI Vision Excel 저장 완료: ai_vision_receipts.xlsx")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()