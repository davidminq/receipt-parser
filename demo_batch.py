#!/usr/bin/env python3
"""
배치 처리 데모 - 시뮬레이션된 이미지들로 테스트
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random
from batch_processor import BatchReceiptProcessor

def create_demo_receipt_images():
    """데모용 영수증 이미지들 생성"""

    print("🎨 데모용 영수증 이미지 생성 중...")

    # 샘플 영수증 데이터
    sample_receipts = [
        {
            "filename": "demo_receipt_1.png",
            "content": [
                "STARBUCKS COFFEE",
                "Grande Latte      $5.45",
                "Blueberry Muffin  $3.25",
                "Total:            $8.70"
            ]
        },
        {
            "filename": "demo_receipt_2.png",
            "content": [
                "McDONALD'S",
                "Big Mac           $4.89",
                "Large Fries       $2.39",
                "Coca Cola         $1.99",
                "Total:            $9.27"
            ]
        },
        {
            "filename": "demo_receipt_3.png",
            "content": [
                "WALMART",
                "Milk 1 Gallon     $3.48",
                "Bread             $2.50",
                "Eggs Dozen        $2.98",
                "Bananas 3lb       $1.78",
                "Total:           $10.74"
            ]
        }
    ]

    created_files = []

    for receipt_data in sample_receipts:
        # 이미지 생성 (흰 배경)
        img = Image.new('RGB', (400, 300), color='white')
        draw = ImageDraw.Draw(img)

        # 텍스트 그리기
        y_pos = 20
        for line in receipt_data["content"]:
            try:
                # 기본 폰트 사용
                draw.text((20, y_pos), line, fill='black')
                y_pos += 25
            except:
                # 폰트 로드 실패시 기본 처리
                draw.text((20, y_pos), line, fill='black')
                y_pos += 25

        # 이미지 저장
        img.save(receipt_data["filename"])
        created_files.append(receipt_data["filename"])
        print(f"   ✅ {receipt_data['filename']} 생성")

    return created_files

def demo_batch_processing():
    """배치 처리 데모 실행"""

    print("\n🚀 배치 처리 데모 시작")
    print("=" * 50)

    # 데모 이미지 생성
    demo_files = create_demo_receipt_images()

    try:
        # 배치 프로세서 초기화
        processor = BatchReceiptProcessor(".")

        # 배치 처리 실행 (자동 모드)
        results = processor.process_all_images()

        # 결과 출력
        if results["success"]:
            print(f"\n🎉 배치 처리 성공!")
            print(f"   처리된 파일: {results['successful']}/{results['total_files']}")

            if results["receipts"]:
                total_amount = sum(r.total_float for r in results["receipts"])
                print(f"   전체 금액: ${total_amount:.2f}")

        return results

    finally:
        # 데모 파일 정리
        print(f"\n🧹 데모 파일 정리 중...")
        for file in demo_files:
            try:
                Path(file).unlink()
                print(f"   🗑️ {file} 삭제")
            except:
                pass

def show_usage_examples():
    """사용 예시 설명"""

    print("\n📋 실제 사용법:")
    print("=" * 30)

    print("\n1️⃣ 기본 사용법:")
    print("   # 현재 폴더의 모든 영수증 처리")
    print("   python3 batch_processor.py")

    print("\n2️⃣ 코드에서 사용:")
    print("   from batch_processor import batch_process_directory")
    print("   results = batch_process_directory('/path/to/images')")

    print("\n3️⃣ 지원 파일 형식:")
    print("   .jpg, .jpeg, .png, .tiff, .bmp")

    print("\n4️⃣ 결과 파일:")
    print("   - batch_receipts_YYYYMMDD.xlsx")
    print("   - 각 영수증별 시트 + 요약 시트")

    print("\n💡 팁:")
    print("   - 여러 영수증을 한 폴더에 모아두고 실행")
    print("   - 파일명은 자동으로 인식")
    print("   - 실패한 파일은 따로 표시됨")

if __name__ == "__main__":
    # 데모 실행
    demo_results = demo_batch_processing()

    # 사용법 설명
    show_usage_examples()