f = open("tempdata.txt")
my_dict = {}
content = f.readline()
while content != "":
    content = content.strip().split("\t")
    if "corrosie" in content[0]:
        pass
    else:
        my_dict[str(content[0].replace(" ", ""))] = [float(x.replace(",", ".")) for x in content[1:]]
    content = f.readline()
f.close()
for x, y in my_dict.items():
  print(f"\"{x}\" : {y},")