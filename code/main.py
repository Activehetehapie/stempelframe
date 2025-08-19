import pandas as pd
import numpy as np

def find_next_table(file):
    content = ''
    while content not in tables_data:
        content = file.readline()
        if content == '':
            return content
        content = content.strip()
    return content

def read_table_contents(file):
    first_content = find_first_content(file)
    if first_content == '':
        return ''
    return extract_all_content(file, first_content)

def find_first_content(file):
    content = file.readline()
    if content == '':
            return content
    content = content.strip()
    while content not in tables_data:
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
        if content == '' or content in tables_data or not content.strip()[0].isnumeric():
            save_pos = file.tell()
            next = file.readline()
            if next == '' or next in tables_data or not next.strip()[0].isnumeric():
                file.seek(pos)
                return table_content
            else:
                file.seek(save_pos)
        table_content.append(content.strip().split())

def make_single_list(table_contents):
    new_list = []
    size = len(table_contents[0])
    for values in table_contents:
        if 0 != len(values) % 2 or size != len(values):
            new_list.append(values)
        else:
            new_list.append(values[:int(len(values)/2)])
            new_list.append(values[int(len(values)/2):])
    return new_list

def fill_table_zero(table_contents, table_name):
    new_list = []
    length = len(tables_data[table_name])
    for value in table_contents:
        if len(value) > length:
            raise Exception("There are more variables than tableheaders. Please review the import format!")
        while len(value) < length:
            value.append("0")
        new_list.append(value)
    return new_list

def knoop_or_pos(table_contents):
    new_list = []
    for values in table_contents:
        if values[0].upper == values[1]:
            new_list.append(values)
            continue
        if values[1].isdecimal():
            values.insert(2, '0')
            new_list.append(values)
        else:
            values.insert(1, '0')
            new_list.append(values)
    return new_list

def fill_in_missing_numbers(table_contents, table_name):
    new_list = []
    current_force = 0
    for values in table_contents:
        if values[1] == '0':
            values.insert(3, current_force)
        else:
            current_force = values[3]
        if len(tables_data[table_name]) != len(values):
            values.insert(5, 0)
        new_list.append(values)
    return new_list


def sort_table(table_contents):
    return sorted(table_contents, key=lambda x: float(x[0]))

def verify_tables(tables):
    for table in tables:
        for item in table[2]:
            if len(item) != len(table[1]) and table[0] != "BELASTINGGEVALLEN" and table[0] != 'BELASTINGCOMBINATIES':
                print(item)
                raise Exception(f"Table verification went failed, table needs {len(table[1])} but has {len(item)} in table {table[0]}")

def clean_key(key):
    dissallowed_excel_characters = [':', '\\', '/', '*', '?', '"', '<', '>', '|', '[', ']']
    for char in dissallowed_excel_characters:
        key = key.replace(char, " ")
    return key

def make_numerical(tables):
    for table in tables:
        for i, item in enumerate(table[2]):
            for j, value in enumerate(item):
                try:
                    num = float(value)
                    if num.is_integer():
                        table[2][i][j] = int(num)
                    else:
                        table[2][i][j] = num
                except Exception:
                    pass

def generate_dataframes(tables):
    dataframes = {}
    for table in tables:
        new_format = {}
        arr = np.array(table[2])
        arr = np.transpose(arr)
        for x in range(len(table[1])):
            new_format[table[1][x]] = arr[x]
        df = pd.DataFrame(new_format)
        dataframes[clean_key(table[0])] = df
    return dataframes


tables_data = {
    'MATERIALEN': ['Mt', 'Kwaliteit', 'E-modulus[N/mm2]', 'S.G.', 'Pois.', 'Uitz. coëff'],
    'PROFIELEN [mm]': ['Prof.', 'Omschrijving', 'Materiaal', 'Oppervlak', 'Traagheid', 'Vormf.'],
    'PROFIELEN vervolg [mm]': ['Prof.', 'Staaftype', 'Breedte', 'Hoogte', 'e', 'Type', 'b1', 'h1', 'b2', 'h2'],
    'PROFIELVORMEN [mm]': ['Prof.', 'Type'],
    'KNOPEN': ['Knoop', 'X', 'Z'],
    'STAVEN': ['St.', 'ki', 'kj', 'Profiel', 'Aansl.i', 'Aansl.j', 'Lengte', 'Opm.'],
    'VEREN': ['Veer', 'Knoop', 'Richting', 'Hoek', 'Veerwaarde', 'Type', 'Bovengrens', 'Ondergrens'],
    'BEDDINGEN': ['Nr.', 'Staven', 'Bedding', 'Breedte[mm]', 'Zijde'],
    'BELASTINGGEVALLEN': ['B.G.', 'Omschrijving', 'Type'],
    'STAAFBELASTINGEN   B.G:1 UGT': ['Last', 'Staaf', 'Type', 'q1/p/m', 'q2', 'A', 'B', 'psi', 'psi-t', 'Opm.'],
    'STAAFBELASTINGEN   B.G:2 BGT': ['Last', 'Staaf', 'Type', 'q1/p/m', 'q2', 'A', 'B', 'psi', 'psi-t', 'Opm.'],
    'STAAFBELASTINGEN   B.G:1 Trek': ['Last', 'Staaf', 'Type', 'q1/p/m', 'q2', 'A', 'B', 'psi', 'psi-t', 'Opm.'],
    'STAAFBELASTINGEN   B.G:2 Druk': ['Last', 'Staaf', 'Type', 'q1/p/m', 'q2', 'A', 'B', 'psi', 'psi-t', 'Opm.'],
    'BELASTINGCOMBINATIES': ['BC', 'Type'],
    'STAAFKRACHTEN  B.C:1 Sterkte': ['St.', 'Kn.', 'Pos.', 'NXi/NXj', 'DZi/DZj', 'MYi/MYj'],
    'STAAFKRACHTEN  B.C:2 Vervorming': ['St.', 'Kn.', 'Pos.', 'NXi/NXj', 'DZi/DZj', 'MYi/MYj'],
    'REACTIES': ['X.', 'Z', 'M'],
    'VERPLAATSINGEN  [mm;rad]  B.C:1 Sterkte': ['Kn.', 'X-verpl.', 'Z-verpl.', 'Rotatie', 'Kn.', 'X-verpl.', 'Z-verpl.', 'Rotatie'],
    'VERPLAATSINGEN  [mm;rad]  B.C:2 Vervorming': ['Kn.', 'X-verpl.', 'Z-verpl.', 'Rotatie', 'Kn.', 'X-verpl.', 'Z-verpl.', 'Rotatie'],
    'TUSSENPUNTEN VERPLAATSINGEN  B.C:2 Vervorming': ['St.', 'Kn.', 'Pos.', 'globaal Verpl-X', 'Verpl-Z', 'lokaal Verpl-X', 'Verpl-Z', 'Rotatie', 'Grondspan.']
}

# settings KN or Pos, single list, missing numbers, missing numbers staaf, sorting

table_settings = {
    'MATERIALEN': [0,0,0,0,0],
    'PROFIELEN [mm]': [0,0,0,0,0],
    'PROFIELEN vervolg [mm]': [0,0,1,0,0],
    'PROFIELVORMEN [mm]': [0,0,0,0,0],
    'KNOPEN': [0,1,0,0,1],
    'STAVEN': [0,0,1,0,0],
    'VEREN': [0,0,0,0,0],
    'BEDDINGEN': [0,0,0,0,0],
    'BELASTINGGEVALLEN': [0,0,0,0,0],
    'STAAFBELASTINGEN   B.G:1 UGT': [0,0,1,0,0],
    'STAAFBELASTINGEN   B.G:2 BGT': [0,0,1,0,0],
    'STAAFBELASTINGEN   B.G:1 Trek': [1,0,0,1,0],
    'STAAFBELASTINGEN   B.G:2 Druk': [1,0,0,1,0],
    'BELASTINGCOMBINATIES': [0,0,0,0,0],
    'STAAFKRACHTEN  B.C:1 Sterkte': [1,0,0,1,0],
    'STAAFKRACHTEN  B.C:2 Vervorming': [1,0,0,1,0],
    'REACTIES': [0,0,0,1,0],
    'VERPLAATSINGEN  [mm;rad]  B.C:1 Sterkte': [0,1,0,0,1],
    'VERPLAATSINGEN  [mm;rad]  B.C:2 Vervorming': [0,1,0,0,1],
    'TUSSENPUNTEN VERPLAATSINGEN  B.C:2 Vervorming': [1,0,1,0,0]
}

# Globals
reading_file = True
input_bestand = r"code\testfiles\input.txt"
output_bestand = r"code\nieuw.xlsx"

tables = []

if __name__ == "__main__":
    with open(input_bestand, 'r') as file:
        while reading_file:
            found_table_name = find_next_table(file)
            if found_table_name == '':
                break
            table_contents = read_table_contents(file)
            if (table_settings[found_table_name][0]):
                table_contents = knoop_or_pos(table_contents)

            if (table_settings[found_table_name][1]):
                table_contents = make_single_list(table_contents)

            if (table_settings[found_table_name][2]):
                table_contents = fill_table_zero(table_contents, found_table_name)

            if (table_settings[found_table_name][3]):
                table_contents = fill_in_missing_numbers(table_contents, found_table_name)

            if (table_settings[found_table_name][4]):
                table_contents = sort_table(table_contents)

            tables.append([found_table_name, tables_data[found_table_name], table_contents])

    verify_tables(tables)
    make_numerical(tables)
    dataframes = generate_dataframes(tables)

    with pd.ExcelWriter(output_bestand, engine='openpyxl') as writer:
        for sheet_name, df in dataframes.items():
            df.to_excel(writer, index=False, sheet_name=sheet_name)
