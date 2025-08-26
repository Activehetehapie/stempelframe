import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

# Sample DataFrame
df = pd.DataFrame({
    'Product': ['Apples', 'Bananas', 'Cherries'],
    'Price': [1.2, 0.85, 2.5],
    'Stock': [100, 150, 75]
})

# Create workbook and sheet
wb = Workbook()
ws = wb.active
ws.title = 'Stempels'

# Write DataFrame to sheet
for r in dataframe_to_rows(df, index=False, header=True):
    ws.append(r)

# Apply Dutch-style number format to float cells
for row in ws.iter_rows(min_row=2):  # Skip header
    for cell in row:
        if isinstance(cell.value, float):
            cell.number_format = '#.##0,00'  # comma as decimal, dot as thousands separator
