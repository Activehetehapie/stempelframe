import pandas as pd

# Bestandspaden instellen
input_file_path = r"C:\Users\Stefan.Grossouw\OneDrive - Van t Hek Beheer\Documenten - HEK-PRJ-H241500-H241599\H241570 - OZ - Aanhechting vulgrout aan paaloppervlak\2 Berekening\Python\import.py\H25.1053-B Koplframe.txt"
output_excel_path = r"C:\Users\Stefan.Grossouw\OneDrive - Van t Hek Beheer\Documenten - HEK-PRJ-H241500-H241599\H241570 - OZ - Aanhechting vulgrout aan paaloppervlak\2 Berekening\Python\import.py\H25.1053-B Koplframe_Parsed.xlsx"

# Lees het tekstbestand
with open(input_file_path, 'r', encoding='latin-1') as file:
    lines = file.readlines()

# Secties definiëren in het bestand
sections = {
    "Materials": "MATERIALEN",
    "Profiles": "PROFIELEN [mm]",
    "Knopen": "KNOPEN",
    "Staven": "STAVEN",
    "Beddings": "BEDDINGEN",
    "Loads": "BELASTINGGEVALLEN",
    "BarLoads": "STAAFBELASTINGEN",
    "BarForces": "STAAFKRACHTEN"
}

# Hulpfunctie om secties te extraheren
def extract_section(lines, section_title, next_section_titles):
    start_index = next((i for i, line in enumerate(lines) if section_title in line), None)
    if start_index is None:
        return None
    
    # Zoek het einde van de huidige sectie
    end_index = next(
        (i for i, line in enumerate(lines[start_index + 1:], start=start_index + 1)
         if any(title in line for title in next_section_titles)),
        len(lines)
    )
    section_data = lines[start_index + 1:end_index]
    return [line.strip() for line in section_data if line.strip()]

# Verwerk de secties
dataframes = {}
section_titles = list(sections.values())

for section_name, section_title in sections.items():
    next_titles = section_titles[section_titles.index(section_title) + 1:]
    section_data = extract_section(lines, section_title, next_titles)
    if section_data:
        # Split de gegevens in tabellen op basis van whitespace
        split_data = [line.split() for line in section_data]
        dataframes[section_name] = pd.DataFrame(split_data)

# Schrijf alle secties naar een Excel-bestand
with pd.ExcelWriter(output_excel_path, engine='openpyxl') as writer:
    for sheet_name, df in dataframes.items():
        df.to_excel(writer, index=False, sheet_name=sheet_name)

output_excel_path

