from typing import List


def get_all_hex_codes(rtf_output: str) -> List[str]:
    """From the .rtf outputfile, return the hexadecimal code of all the wmf pictures in a list"""
    list_hexacodes = []
    switch = False
    hexacode = ""
    for line in rtf_output.splitlines():
        if not switch:
            if "wmetafile8" in line:
                switch = True
                hexacode = ""
                continue
        else:
            if "par" in line:
                switch = False
                list_hexacodes.append(hexacode)
                continue
            hexacode = hexacode + line

    return list_hexacodes


def make_rtf_string_content(number_of_materials: int, rtf_output: str) -> str:
    """recreate a shorter rtf string content to be displayed within the app"""
    list_hex = get_all_hex_codes(rtf_output)
    moment_bc1_hex = list_hex[11 + number_of_materials]
    shear_bc_1_hex = list_hex[12 + number_of_materials]

    stringcontent = (
        r"{\rtf1\ansi"
        + "\n"
        + add_section("bc1")
        + add_title("MOMENTEN", "bc1")
        + add_image(moment_bc1_hex)
        + add_title("DWARSKRACHTEN", "bc1")
        + add_image(shear_bc_1_hex)
        + "\page"
        + add_title("NORMAALKRACHTEN", "bc1")
        + add_image(list_hex[13 + number_of_materials])
        + add_title("VERPLAATSINGEN", "bc1")
        + add_image(list_hex[14 + number_of_materials])
        + "\page"
        + add_section("bc2")
        + add_title("MOMENTEN", "bc2")
        + add_image(list_hex[15 + number_of_materials])
        + add_title("DWARSKRACHTEN", "bc2")
        + add_image(list_hex[16 + number_of_materials])
        + "\page"
        + add_title("NORMAALKRACHTEN", "bc2")
        + add_image(list_hex[17 + number_of_materials])
        + add_title("VERPLAATSINGEN", "bc2")
        + add_image(list_hex[18 + number_of_materials])
        + "}"
    )

    return stringcontent


def add_section(load_combination: str) -> str:
    if load_combination == "bc1":
        string = (
            r"\pard {\brdrb\brdrs\brdrw15\brsp20\brdrbtw\brdrs"
            + r"{\f0\fs28 \b BELASTINGCOMBINATIE}"
            + "\n"
            + r"{\f0\fs28                        \b B.C:1}"
            + r"{\f0\fs28  \b Sterkte}"
            + "\par}"
            + r"\f0\fs20\par\pard"
        )
    else:
        string = (
            r"\pard {\brdrb\brdrs\brdrw15\brsp20\brdrbtw\brdrs"
            + r"{\f0\fs28 \b BELASTINGCOMBINATIE}"
            + "\n"
            + r"{\f0\fs28                        \b B.C:2}"
            + r"{\f0\fs28  \b Vervorming}"
            + "\par}"
            + r"\f0\fs20\par\pard"
        )
    return string


def add_title(variable: str, load_combination: str) -> str:
    if load_combination == "bc1":
        string = (
            r"\pard {"
            + r"{\f0\fs28 \b "
            + f"{variable}"
            + "}"
            + "\n"
            + r"{\f0\fs20                                                     B.C:1}"
            + r"{\f0\fs20  Sterkte}"
            + r"\par}"
            + r"\f0\fs20\par\pard"
        )
    else:
        string = (
            r"\pard {"
            + r"{\f0\fs28 \b "
            + f"{variable}"
            + "}"
            + "\n"
            + r"{\f0\fs20                                                     B.C:2}"
            + r"{\f0\fs20  Vervorming}"
            + r"\par}"
            + r"\f0\fs20\par\pard"
        )

    return string


def add_image(hex: str) -> str:
    string = (
        r"{\pard\pict\picw17000\pich7180\picwgoal9638\pichgoal4071\wmetafile8"
        + "\n"
        + hex
        + "\n}\par"
    )
    return string
