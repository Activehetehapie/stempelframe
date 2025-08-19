def first_table(file):
    content = file.readline().split()
    while (content[0].isupper() != True):
        content = file.readline()
    return content

def extract_column_names(file):
    column_names = file.readline().split()
    print(column_names)

def extract_table(file):
    file.readline()
    extract_column_names(file)


tables = {}
file = open("bestand.txt", 'r')
table_name = first_table(file)
extract_table(file)

print(tables)
