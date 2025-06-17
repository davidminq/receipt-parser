import re

def parse_receipt_text(text):
    """
    영수증 텍스트에서 항목명과 금액을 추출하는 함수
    예: "Starbucks $25.43" → ("Starbucks", 25.43)
    """
    lines = text.splitlines()
    cleaned_data = []

    for line in lines:
        match = re.search(r"(.*?)(\$?\s?\d+\.\d{2})", line)
        if match:
            item = match.group(1).strip()
            amount = match.group(2).replace("$", "").strip()
            try:
                amount = float(amount)
                cleaned_data.append((item, amount))
            except ValueError:
                continue

    return cleaned_data