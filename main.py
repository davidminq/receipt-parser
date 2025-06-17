import re
from ocr_parser import extract_text_from_image
from excel_writer import save_to_excel
from receipt_cleaner import parse_receipt_text
import datetime

def extract_date_from_text(text):
    # Simple pattern for dates like YYYY-MM-DD or MM/DD/YYYY
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

# OCR 돌리기
text = extract_text_from_image("screenshots/IMG_5336.png")
receipt_date = extract_date_from_text(text)

# 항목 + 금액 파싱
raw_data = parse_receipt_text(text)
parsed_data = raw_data

# 금액만 추출
amounts = [amount for _, amount in parsed_data]
total = sum(amounts)

# 출력
print("🧾 추출된 항목 및 금액들:")
for item, amount in parsed_data:
    print(f"- {item}: ${amount:.2f}")
print(f"\n💵 총합: ${total:.2f}")

# 엑셀 저장
save_to_excel(parsed_data, receipt_date)
print("✅ 엑셀 저장 완료: receipts.xlsx")