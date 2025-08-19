import pandas as pd

input_bestand = r"bestand.txt"
output_bestand = r"C:\txtToExcelAutomation\bestand.xlsx"


tables = {
    'MATERIALEN': ['Mt', 'Kwaliteit', 'E-modulus[N/mm2]', 'S.G.', 'Pois.', 'Uitz. coëff'],
    'PROFIELEN [mm]': ['Prof.', 'Omschrijving', 'Materiaal', 'Oppervlak', 'Traagheid', 'Vormf.'],
    'PROFIELEN vervolg [mm]': ['Prof.', 'Staaftype', 'Breedte', 'Hoogte', 'e', 'Type', 'b1', 'h1', 'b2', 'h2'],
    'PROFIELVORMEN [mm]': ['Prof.', 'Type'],
    'KNOPEN': ['Knoop', 'X', 'Z'],
    'STAVEN': ['St.', 'ki', 'kj', 'Profiel', 'Aansl.i', 'Aansl.j', 'Lengte', 'Opm.'],
    'VEREN': ['Veer', 'Knoop', 'Richting', 'Hoek', 'Veerwaarde', 'Type', 'Bovengrens', 'Ondergrens'],
    'BEDDINGEN': ['Nr.', 'Staven', 'Bedding', 'Breedte[mm]', 'Zijde'],
    'BELASTINGGEVALLEN': ['B.G.', 'Omschrijving', 'Type'],
    'STAAFBELASTINGEN B.G:1 UGT': ['Last', 'Staaf', 'Type', 'q1/p/m', 'q2', 'A', 'B', 'psi', 'psi-t', 'Opm.'],
    'STAAFBELASTINGEN B.G:2 BGT': ['Last', 'Staaf', 'Type', 'q1/p/m', 'q2', 'A', 'B', 'psi', 'psi-t', 'Opm.'],
    'STAAFBELASTINGEN   B.G:1 Trek': ['Last', 'Staaf', 'Type', 'q1/p/m', 'q2', 'A', 'B', 'psi', 'psi-t', 'Opm.'],
    'STAAFBELASTINGEN   B.G:2 Druk': ['Last', 'Staaf', 'Type', 'q1/p/m', 'q2', 'A', 'B', 'psi', 'psi-t', 'Opm.'],
    'BELASTINGCOMBINATIES': ['BC', 'Type'],
    'STAAFKRACHTEN  B.C:1 Sterkte': ['St.', 'Kn.', 'Pos.', 'NXi/NXj', 'DZi/DZj', 'MYi/MYj'],
    'STAAFKRACHTEN  B.C:2 Vervorming': ['St.', 'Kn.', 'Pos.', 'NXi/NXj', 'DZi/DZj', 'MYi/MYj'],
    'REACTIES': ['X.', 'Z', 'M']
}
generated_tables = {}
reading_file = True

def clean_key(key):
    dissallowed_excel_characters = [':', '\\', '/', '*', '?', '"', '<', '>', '|', '[', ']']
    for char in dissallowed_excel_characters:
        key = key.replace(char, " ")        
    return key

def refactor_data():
    reformated_data = {}
    for key, value in generated_tables.items():
        new_dict_format = {}
        number_of_columns = len(tables[key])
        for x in range(0, number_of_columns):
            column = []
            for item in value:
                if x >= len(item):
                    column.append(0)
                else:
                    column.append(item[x])
            new_dict_format[tables[key][x]] = column
        df = pd.DataFrame(new_dict_format)
        cleaned_key = clean_key(key)
        reformated_data[cleaned_key] = df
    generated_tables.clear()
    return reformated_data


def find_next_table(file):
    content = file.readline()
    if content == '':
            return content
    content = content.strip()
    while content not in tables:
        content = file.readline()
        if content == '':
            return content
        content = content.strip()
    return content

def find_first_content(file):
    content = file.readline()
    if content == '':
            return content
    content = content.strip()
    while content not in tables:
        content = file.readline()
        if content == '':
            return content
        content = content.strip()
        if content != '':
            if content[0].isnumeric():
                return content.split()
            
def extract_all_content(file, first_content):
    table_content = [first_content]
    while True:
        pos = file.tell()
        content = file.readline()
        if content == '' or content in tables or not content.strip()[0].isnumeric():
            file.seek(pos)
            return table_content
        table_content.append(content.strip().split())

def read_table_contents(file):
    first_content = find_first_content(file)
    if first_content == '':
        return ''
    return extract_all_content(file, first_content)

def make_long_list():
    for key, value in generated_tables.items():
        for item in value:
            if len(item) % len(tables[key]) == 0 and len(item) > len(tables[key]):
                if item[0].isnumeric() and not item[len(tables[key])].isnumeric():
                    break
                equal_columns = len(item) / len(tables[key])
                new_list = []
                while equal_columns != 1:
                    equal_columns -= 1
                    count = 0
                    new_list.clear()
                    while count < len(tables[key]):
                        count += 1
                        list_item = item.pop(len(tables[key]))
                        new_list.append(list_item)
                value.append(new_list)

def set_item_correctly():
    make_long_list()

def sort_items():
    for key,value in generated_tables.items():
        value.sort(key=lambda x: int(x[0]))
            


with open(input_bestand, 'r') as file:
    while reading_file:
        found_table_name = find_next_table(file)
        if found_table_name == '':
            break
        table_contents = read_table_contents(file)
        generated_tables[found_table_name] = table_contents

set_item_correctly()
sort_items()

# for key, value in generated_tables.items():
#     print(key)
#     for item in value:
#         print(item)

reformated_data = refactor_data()

with pd.ExcelWriter(output_bestand, engine='openpyxl') as writer:
    for sheet_name, df in reformated_data.items():
        df.to_excel(writer, index=False, sheet_name=sheet_name)