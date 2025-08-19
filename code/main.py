#import pandas as pd

def find_next_table(file):
    content = ''
    while content not in tables:
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
    'REACTIES': ['X.', 'Z', 'M'],
    'VERPLAATSINGEN  [mm;rad]  B.C:1 Sterkte': ['Kn.', 'X-verpl.', 'Z-verpl.', 'Rotatie', 'Kn.', 'X-verpl.', 'Z-verpl.', 'Rotatie'],
    'VERPLAATSINGEN  [mm;rad]  B.C:2 Vervorming': ['Kn.', 'X-verpl.', 'Z-verpl.', 'Rotatie', 'Kn.', 'X-verpl.', 'Z-verpl.', 'Rotatie'],
    'TUSSENPUNTEN VERPLAATSINGEN  B.C:2 Vervorming': ['St.', 'Kn.', 'Pos.', 'globaal Verpl-X', 'Verpl-Z', 'lokaal Verpl-X', 'Verpl-Z', 'Rotatie Grondspan.']
}

# settings single list, missing numbers, sorting

table_settings = {
    'MATERIALEN': [0,0,0],
    'PROFIELEN [mm]': [0,0,0],
    'PROFIELEN vervolg [mm]': [0,1,0],
    'PROFIELVORMEN [mm]': [0,0,0],
    'KNOPEN': [1,0,1],
    'STAVEN': [0,0,0],
    'VEREN': [0,0,0],
    'BEDDINGEN': [0,0,0],
    'BELASTINGGEVALLEN': [],
    'STAAFBELASTINGEN B.G:1 UGT': [0,1,0],
    'STAAFBELASTINGEN B.G:2 BGT': [0,1,0],
    'STAAFBELASTINGEN   B.G:1 Trek': [],
    'STAAFBELASTINGEN   B.G:2 Druk': [],
    'BELASTINGCOMBINATIES': [0,0,0],
    'STAAFKRACHTEN  B.C:1 Sterkte': [0,1,0],
    'STAAFKRACHTEN  B.C:2 Vervorming': [0,1,0],
    'REACTIES': [0,1,0],
    'VERPLAATSINGEN  [mm;rad]  B.C:1 Sterkte': [1,0,1],
    'VERPLAATSINGEN  [mm;rad]  B.C:2 Vervorming': [1,0,1],
    'TUSSENPUNTEN VERPLAATSINGEN  B.C:2 Vervorming': [0,1,0]
}

# Globals
reading_file = True
input_bestand = r"code\testfiles\input.txt"
output_bestand = r"code\bestand.xlsx"

if __name__ == "__main__":
    with open(input_bestand, 'r') as file:
        while reading_file:
            found_table_name = find_next_table(file)
            if found_table_name == '':
                break
            table_contents = read_table_contents(file)
            for item in table_contents:
                print(item)
            print("\n")