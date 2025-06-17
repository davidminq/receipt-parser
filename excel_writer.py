import pandas as pd
from datetime import datetime
import os

def save_to_excel(data, receipt_date, file_path=None):
    if file_path is None:
        file_path = 'receipts.xlsx'

    # Create a DataFrame from the list of (업체명, amount) tuples
    df = pd.DataFrame(data, columns=['업체명', '금액 ($)'])
    df['카테고리'] = ''  # Placeholder for category to be filled later
    df['날짜'] = receipt_date.strftime('%Y-%m-%d')
    df = df[['날짜', '업체명', '카테고리', '금액 ($)']]

    # Add a total row
    total = df['금액 ($)'].sum()
    df.loc[len(df)] = [receipt_date.strftime('%Y-%m-%d'), '총합', '', total]

    # Sheet name based on receipt date
    sheet_name = 'Receipt ' + receipt_date.strftime('%Y-%m-%d')

    # Save or overwrite Excel file
    if os.path.exists(file_path):
        with pd.ExcelWriter(file_path, engine='openpyxl', mode='w') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
