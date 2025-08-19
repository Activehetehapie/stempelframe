from io import StringIO
from pathlib import Path
from typing import Dict, Tuple, Optional

from munch import Munch
from numpy import arange, nan, pi, sqrt, inf
from pandas import DataFrame
import pandas as pd

from app.XMLupload.constants import (
    γm_gording_UGT,
    M0,
    columns_results_purlins,
    columns_calculations_purlins)
from viktor import UserError


def get_profiles_table():
    path_ = Path(__file__).parent / "tabel_profielen.csv"
    with open(path_, "r") as f:
        file_content = f.read()
    csvfile = StringIO(file_content)
    df_table_profiles = pd.read_csv(csvfile, delimiter=";")
    return df_table_profiles


def get_df_calculations_purlins(
    technosoft_parsed_outputs: Dict[str, DataFrame], params: Munch
) -> Optional[DataFrame]:
    df_barforces_UGT = technosoft_parsed_outputs["df_barforces_UGT"]
    df_barforces_BGT = technosoft_parsed_outputs["df_barforces_BGT"]
    df_bars = technosoft_parsed_outputs["df_bars"]
    df_profiles = technosoft_parsed_outputs["df_profiles"]
    df_barloads_UGT = technosoft_parsed_outputs["df_barloads_UGT"]
    df_barloads_BGT = technosoft_parsed_outputs["df_barloads_BGT"]
    df_nodes = technosoft_parsed_outputs["df_nodes"]
    df_supports = technosoft_parsed_outputs["df_supports"]

    m_factor = params.m_factor
    if not m_factor:
        raise UserError("Vul Moment factor op tabblad \"Invoer Berekening\" in")

    dict_bars = df_bars.set_index("St.").to_dict()
    dict_profiles = df_profiles.set_index("Prof.").to_dict()
    dict_barloads_UGT = df_barloads_UGT.set_index("Staaf").to_dict()
    dict_barloads_BGT = df_barloads_BGT.set_index("Staaf").to_dict()

    df_calculations_purlins = df_barforces_UGT.copy()
    df_calculations_purlins.insert(5, "N_BGT", df_barforces_BGT["NXi/NXj"])
    df_calculations_purlins["N_BGT"] = df_calculations_purlins["N_BGT"].replace(
        "", method="ffill"
    )
    df_calculations_purlins.insert(6, "M_BGT", df_barforces_BGT["MYi/MYj"])
    df_calculations_purlins = df_calculations_purlins[
        df_calculations_purlins["DZi/DZj"].notna()
    ]

    df_calculations_purlins.insert(
        1, "Profiel", df_calculations_purlins["St."].map(dict_bars["Profiel"])
    )
    split_profile_UGT_purlin = df_calculations_purlins["Profiel"].str.split(
        "[:]", expand=True
    )

    df_calculations_purlins.insert(2, "ID_sterkte", split_profile_UGT_purlin[0])
    df_calculations_purlins.insert(3, "Profiel_", split_profile_UGT_purlin[1])
    df_calculations_purlins.insert(
        4,
        "Sterkteklasse",
        df_calculations_purlins["ID_sterkte"].map(dict_profiles["Materiaal_"]),
    )
    df_calculations_purlins["Sterkteklasse"] = df_calculations_purlins[
        "Sterkteklasse"
    ].astype(float)
    df_calculations_purlins = df_calculations_purlins[
        df_calculations_purlins.Profiel_.str[0] != "B"
    ]

    df_rename_profile_purlin = DataFrame(
        data=df_calculations_purlins["Profiel_"], columns=["Profiel_", "Profiel_naam"]
    )
    df_rename_profile_purlin.insert(1, "n_prof", "1X")
    list_profile_name = []
    for row_1 in df_rename_profile_purlin["Profiel_"]:
        if row_1[0] == "H":
            list_profile_name.append("1X" + row_1)
        else:
            list_profile_name.append(row_1)
    df_rename_profile_purlin["Profiel_naam"] = list_profile_name
    df_calculations_purlins.insert(
        4, "Profiel_naam", df_rename_profile_purlin["Profiel_naam"]
    )
    df_calculations_purlins.insert(
        5, "n_profiles", df_calculations_purlins.Profiel_naam.str[0]
    )
    df_calculations_purlins["n_profiles"] = df_calculations_purlins[
        "n_profiles"
    ].astype(float)
    df_calculations_purlins.insert(
        6, "profiel_naam", df_calculations_purlins.Profiel_naam.str[2:]
    )
    df_calculations_purlins["profiel_naam"] = (
        df_calculations_purlins.profiel_naam.str[:3]
        + " "
        + df_calculations_purlins.profiel_naam.str[3:]
    )

    df_calculations_purlins.insert(
        7,
        "UGT_stempelkracht",
        df_calculations_purlins["St."].map(dict_barloads_UGT["q1/p/m"]),
    )
    df_calculations_purlins.insert(
        7,
        "BGT_stempelkracht",
        df_calculations_purlins["St."].map(dict_barloads_BGT["q1/p/m"]),
    )
    df_calculations_purlins["BGT_stempelkracht"] = df_calculations_purlins[
        "BGT_stempelkracht"
    ].astype(float)
    df_calculations_purlins.insert(11, "N_druk", "")  # -
    df_calculations_purlins.insert(12, "N_trek", "")  # +
    df_calculations_purlins["NXi/NXj"] = pd.to_numeric(
        df_calculations_purlins["NXi/NXj"], errors="coerce"
    )
    list_purlins_N_trek = []
    list_purlins_N_druk = []
    for index_1, row_1 in df_calculations_purlins.iterrows():
        if row_1["NXi/NXj"] <= 0:
            list_purlins_N_druk.append(row_1["NXi/NXj"])
            list_purlins_N_trek.append(0)
        else:
            list_purlins_N_druk.append(0)
            list_purlins_N_trek.append(row_1["NXi/NXj"])
    df_calculations_purlins["N_druk"] = list_purlins_N_druk
    df_calculations_purlins["N_druk"] = abs(df_calculations_purlins["N_druk"])
    df_calculations_purlins["N_trek"] = list_purlins_N_trek
    df_calculations_purlins["DZi/DZj"].replace("", 0, inplace=True)
    df_calculations_purlins["DZi/DZj"] = abs(
        df_calculations_purlins["DZi/DZj"].astype(float)
    )
    df_calculations_purlins["MYi/MYj"].replace("", 0, inplace=True)
    df_calculations_purlins["MYi/MYj"] = abs(
        df_calculations_purlins["MYi/MYj"].astype(float)
    )
    df_calculations_purlins.insert(15, "hoh", "")
    df_calculations_purlins.insert(16, "m_factor", "")
    df_calculations_purlins.insert(
        17,
        "Naam",
        "Staaf nr: "
        + df_calculations_purlins["St."]
        + ", Kn. Pos."
        + df_calculations_purlins["Kn. Pos."],
    )

    dict_ki = {
        ID: ki for ID, ki in zip(dict_bars["ki"].keys(), dict_bars["ki"].values())
    }
    dict_kj = {
        ID: ki for ID, ki in zip(dict_bars["kj"].keys(), dict_bars["kj"].values())
    }
    dict_aansl_i = {
        ID: ki
        for ID, ki in zip(dict_bars["Aansl.i"].keys(), dict_bars["Aansl.i"].values())
    }
    dict_aansl_j = {
        ID: ki
        for ID, ki in zip(dict_bars["Aansl.j"].keys(), dict_bars["Aansl.j"].values())
    }
    dict_lengte = {
        ID: ki
        for ID, ki in zip(dict_bars["Lengte"].keys(), dict_bars["Lengte"].values())
    }
    df_calculations_purlins.insert(1, "ki", df_calculations_purlins["St."].map(dict_ki))
    df_calculations_purlins.insert(2, "kj", df_calculations_purlins["St."].map(dict_kj))
    df_calculations_purlins.insert(
        3, "Aansl.i", df_calculations_purlins["St."].map(dict_aansl_i)
    )
    df_calculations_purlins.insert(
        4, "Aansl.j", df_calculations_purlins["St."].map(dict_aansl_j)
    )
    df_calculations_purlins.insert(
        5, "Lengte", df_calculations_purlins["St."].map(dict_lengte)
    )

    try:
        df_calculations_purlins["ki"] = df_calculations_purlins["ki"].astype(int)
        df_calculations_purlins["kj"] = df_calculations_purlins["kj"].astype(int)
    except ValueError:
        return None
    dict_node_x, dict_node_z = get_nodes_dict_x_z(df_nodes)
    df_calculations_purlins.insert(2, "ki_def", "")
    df_calculations_purlins.insert(4, "kj_def", "")
    df_calculations_purlins.insert(
        2, "ki_x", df_calculations_purlins["ki"].map(dict_node_x)
    )
    df_calculations_purlins.insert(
        3, "ki_z", df_calculations_purlins["ki"].map(dict_node_z)
    )
    df_calculations_purlins.insert(
        6, "kj_x", df_calculations_purlins["kj"].map(dict_node_x)
    )
    df_calculations_purlins.insert(
        7, "kj_z", df_calculations_purlins["kj"].map(dict_node_z)
    )

    dict_m_new = []
    for row_1 in params.general.beams.staven:
        dict_m_new.append(
            {"ID": int(row_1["id"]), "m_factor": m_factor, "hoh": row_1["hoh"]}
        )
    dict_hoh_new = {
        ID: factor
        for ID, factor in zip(
            [id["ID"] for id in dict_m_new], [factor["hoh"] for factor in dict_m_new]
        )
    }
    try:
        df_calculations_purlins["hoh"] = (
            df_calculations_purlins["St."].astype(int).map(dict_hoh_new)
        )
    except ValueError:
        return None
    df_calculations_purlins["hoh"] = df_calculations_purlins["hoh"].str.replace(
        ",", "."
    )
    try:
        df_calculations_purlins["hoh"] = df_calculations_purlins["hoh"].astype(float)
    except ValueError:
        raise UserError(
            "Fout: Voer h.o.h. afstand gording en momentfactor in bij tab: Invoer geometrie > staven"
        )

    df_calculations_m_factor = df_calculations_purlins.copy()
    df_calculations_m_factor = df_calculations_m_factor.drop_duplicates(
        subset="St.", keep="first"
    )

    # uitkragende staven bepalen
    list_number = []
    list_duplicate = []
    dict_node_bar_m_factor = {}
    list_ki = []
    list_kj = []
    for row_1, row_2 in zip(
        df_calculations_m_factor["ki"], df_calculations_m_factor["kj"]
    ):
        list_number.append(row_1)
        list_number.append(row_2)
        list_ki.append(row_1)
        list_kj.append(row_2)

    for i in list_number:
        if i in list_number:
            if i not in list_duplicate:
                list_duplicate.append(i)
            else:
                dict_node_bar_m_factor.update({i: "continuous"})

    df_supports["Knoop"] = df_supports["Knoop"].astype(int)
    for index_1, row_1 in df_supports.iterrows():
        if row_1["Kode XZR 1-vast 0=vrij"] == "100":
            dict_node_bar_m_factor.update({row_1["Knoop"]: "continuous"})

    dict_cantilevered_node = {
        ID: node
        for ID, node in zip(
            dict_node_bar_m_factor.keys(), dict_node_bar_m_factor.values()
        )
    }
    df_calculations_purlins["ki_def"] = df_calculations_purlins["ki"].map(
        dict_cantilevered_node
    )
    df_calculations_purlins["ki_def"] = df_calculations_purlins["ki_def"].replace(
        nan, "cantilevered"
    )
    df_calculations_purlins["kj_def"] = df_calculations_purlins["kj"].map(
        dict_cantilevered_node
    )
    df_calculations_purlins["kj_def"] = df_calculations_purlins["kj_def"].replace(
        nan, "cantilevered"
    )

    # bepalen uitkragendeliggers
    purlins_cantilevered_bars = []  # lijst met uitkragende liggers
    for row_1, row_2, row_3 in zip(
        df_calculations_purlins["ki_def"],
        df_calculations_purlins["kj_def"],
        df_calculations_purlins["St."],
    ):
        if row_1 == "cantilevered":
            purlins_cantilevered_bars.append(row_3)
        if row_2 == "cantilevered":
            purlins_cantilevered_bars.append(row_3)

    list_number_continues_bars = []
    for row_1, row_2, row_3 in zip(
        df_calculations_m_factor["Aansl.i"],
        df_calculations_m_factor["Aansl.j"],
        df_calculations_m_factor["St."],
    ):
        if row_1 == "NDM" and row_2 == "NDM":
            list_number_continues_bars.append(row_3)
    list_number_continues_bars = [
        x for x in list_number_continues_bars if x not in purlins_cantilevered_bars
    ]

    # bepalen eindliggers
    list_end_nodes = []
    for row_1, row_2, row_3, row_4 in zip(
        df_calculations_purlins["Aansl.i"],
        df_calculations_purlins["Aansl.j"],
        df_calculations_purlins["ki"],
        df_calculations_purlins["kj"],
    ):
        if row_1 == "ND":
            list_end_nodes.append(row_3)
        if row_2 == "ND":
            list_end_nodes.append(row_4)
    dict_end_bars = {}
    for index_1, row_1 in df_calculations_purlins.iterrows():
        if row_1["Aansl.i"] == "ND":
            dict_end_bars.update({row_1["St."]: "end"})
        if row_1["Aansl.j"] == "ND":
            dict_end_bars.update({row_1["St."]: "end"})

    list_end_bars = []
    for row_1, row_2, row_3 in zip(
        df_calculations_m_factor["ki_def"],
        df_calculations_m_factor["kj_def"],
        df_calculations_m_factor["St."],
    ):
        if row_1 == "end":
            list_end_bars.append(row_3)
        if row_2 == "end":
            list_end_bars.append(row_3)

    list_end_bars = [x for x in list_end_bars if x not in purlins_cantilevered_bars]

    list_number_continues_bars = [
        x for x in list_number_continues_bars if x not in list_end_bars
    ]  # not used ?

    list_end_bars_ = []  # lijst met eindliggers
    for i in list_end_bars:
        if i not in list_end_bars_:
            list_end_bars_.append(i)

    dict_m_factor_new = {
        ID: factor
        for ID, factor in zip(
            [id["ID"] for id in dict_m_new],
            [factor["m_factor"] for factor in dict_m_new],
        )
    }
    df_split_m_factor = DataFrame(
        data=None, columns=["St.", "m_factor_str", "m_split_1", "m_split_2", "m_factor"]
    )
    df_split_m_factor["St."] = df_calculations_purlins["St."]
    df_split_m_factor["St."] = df_split_m_factor["St."].astype(int)
    df_split_m_factor["m_factor_str"] = df_split_m_factor["St."].map(dict_m_factor_new)
    df_split_m = df_split_m_factor["m_factor_str"].str.split("[/]", expand=True)
    try:
        df_split_m[0] = df_split_m[0].astype(float)
        df_split_m[1] = df_split_m[1].astype(float)
        df_calculations_purlins["m_factor"] = df_split_m[0] / df_split_m[1]
    except ValueError:
        pass

    # START BEREKENINGEN GORDINGEN (start calculations pulinds ??)
    add_profile_parameters_to_df(df_calculations_purlins, "profiel_naam")

    df_calculations_purlins.insert(
        43, "ε", (235 / df_calculations_purlins["Sterkteklasse"])**0.5
    )
    df_calculations_purlins.insert(
        44, "λ1", (pi * sqrt(210000 / df_calculations_purlins["Sterkteklasse"]))
    )
    df_calculations_purlins.insert(
        45,
        "lijf c/t/ε",
        (
            (
                df_calculations_purlins["h"]
                - df_calculations_purlins["tf"]
                - df_calculations_purlins["tf"]
                - df_calculations_purlins["r"]
                - df_calculations_purlins["r"]
            )
            / df_calculations_purlins["tw"]
            / df_calculations_purlins["ε"]
        ),
    )
    df_calculations_purlins.insert(
        46,
        "flens c/t/ε",
        (
            (
                df_calculations_purlins["b"] / 2
                - df_calculations_purlins["tw"] / 2
                - df_calculations_purlins["r"]
            )
            / df_calculations_purlins["tf"]
            / df_calculations_purlins["ε"]
        ),
    )
    # STEMPELUITVAL
    df_calculations_purlins.insert(
        47,
        "MR_rep",
        (
            df_calculations_purlins["m_factor"]
            * df_calculations_purlins["BGT_stempelkracht"]
            * (2 * df_calculations_purlins["hoh"]) ** 2
        ),
    )
    list_drsn_kl_lijf_buiging = []
    for index_1, row_1 in df_calculations_purlins.iterrows():
        if row_1["lijf c/t/ε"] <= 72:
            list_drsn_kl_lijf_buiging.append(1)
        if 72 < row_1["lijf c/t/ε"] <= 83:
            list_drsn_kl_lijf_buiging.append(2)
        if 83 < row_1["lijf c/t/ε"] <= 124:
            list_drsn_kl_lijf_buiging.append(3)
        if row_1["lijf c/t/ε"] > 124:
            list_drsn_kl_lijf_buiging.append(4)
    df_calculations_purlins.insert(48, "drsn. kl. lijf_buiging", 0)
    df_calculations_purlins["drsn. kl. lijf_buiging"] = list_drsn_kl_lijf_buiging
    list_purlins_Wyy = []
    for index_1, row_1 in df_calculations_purlins.iterrows():
        if row_1["drsn. kl. lijf_buiging"] < 3:
            list_purlins_Wyy.append(row_1["Wy_pl"])
        else:
            list_purlins_Wyy.append(row_1["Wy_el"])
    df_calculations_purlins.insert(49, "Wyy", 0)
    df_calculations_purlins["Wyy"] = list_purlins_Wyy
    df_calculations_purlins.insert(
        50,
        "MRd",
        (
            (df_calculations_purlins["Wyy"] * df_calculations_purlins["Sterkteklasse"])
            / M0
            / 1000000
        ),
    )
    df_calculations_purlins.insert(
        51,
        "uc_MR_rep_ME_rep",
        (
            df_calculations_purlins["MR_rep"]
            / df_calculations_purlins["MRd"]
            * df_calculations_purlins["n_profiles"]
        ),
    )
    # """ TOETSING VAN DOORSNEDE """
    # """ TOETSING AXIALE TREK/DRUK """
    df_calculations_purlins.insert(
        52,
        "NEd_trek",
        (
            (df_calculations_purlins["N_trek"] * γm_gording_UGT)
            / df_calculations_purlins["n_profiles"]
        ),
    )
    df_calculations_purlins.insert(
        53,
        "NRd",
        (
            (df_calculations_purlins["A"] * df_calculations_purlins["Sterkteklasse"])
            / M0
            / 1000
        ),
    )
    df_calculations_purlins.insert(
        54,
        "uc_NEd_trek_Nt_Rd",
        (df_calculations_purlins["NEd_trek"] / df_calculations_purlins["NRd"]),
    )
    df_calculations_purlins.insert(
        55,
        "NEd_druk",
        (
            (df_calculations_purlins["N_druk"] * γm_gording_UGT)
            / df_calculations_purlins["n_profiles"]
        ),
    )
    df_calculations_purlins.insert(
        56,
        "uc_NEd_druk_Nc_Rd",
        (df_calculations_purlins["NEd_druk"] / df_calculations_purlins["NRd"]),
    )
    # """ TOETSING BUIGEND MOMENT """
    df_calculations_purlins.insert(
        57,
        "MEd",
        (
            (df_calculations_purlins["MYi/MYj"] * γm_gording_UGT)
            / df_calculations_purlins["n_profiles"]
        ),
    )
    df_calculations_purlins.insert(
        58,
        "uc_MEd_MRd",
        (df_calculations_purlins["MEd"] / df_calculations_purlins["MRd"]),
    )
    # """ TOETSING DWARSKRACHT """
    df_calculations_purlins.insert(
        59,
        "VEd",
        (
            (df_calculations_purlins["DZi/DZj"] * γm_gording_UGT)
            / df_calculations_purlins["n_profiles"]
        ),
    )
    list_drsn_kl_lijf_druk = []
    for index_1, row_1 in df_calculations_purlins.iterrows():
        if row_1["lijf c/t/ε"] <= 33:
            list_drsn_kl_lijf_druk.append(1)
        if 33 < row_1["lijf c/t/ε"] <= 38:
            list_drsn_kl_lijf_druk.append(2)
        if 38 < row_1["lijf c/t/ε"] <= 42:
            list_drsn_kl_lijf_druk.append(3)
        if row_1["lijf c/t/ε"] > 42:
            list_drsn_kl_lijf_druk.append(4)
    df_calculations_purlins.insert(60, "drsn. kl. lijf_druk", 0)
    df_calculations_purlins["drsn. kl. lijf_druk"] = list_drsn_kl_lijf_druk
    df_calculations_purlins.insert(
        61,
        "Av",
        (
            df_calculations_purlins["A"]
            - (2 * df_calculations_purlins["b"] * df_calculations_purlins["tf"])
            + (
                (df_calculations_purlins["tw"] + 2 * df_calculations_purlins["r"])
                * df_calculations_purlins["tf"]
            )
        ),
    )
    df_calculations_purlins.insert(
        62,
        "hw",
        (
            df_calculations_purlins["h"]
            - df_calculations_purlins["tf"]
            - df_calculations_purlins["tf"]
        ),
    )
    df_calculations_purlins.insert(
        63, "Aw", (df_calculations_purlins["hw"] * df_calculations_purlins["tw"])
    )
    list_purlins_A = []
    for index_1, row_1 in df_calculations_purlins.iterrows():
        if row_1["drsn. kl. lijf_druk"] < 3:
            list_purlins_A.append(row_1["Av"])
        else:
            list_purlins_A.append(row_1["Aw"])
    df_calculations_purlins.insert(64, "A_Vc_Rd,", 0)
    df_calculations_purlins["A_Vc_Rd"] = list_purlins_A
    df_calculations_purlins.insert(
        65,
        "Vc_Rd",
        (
            (
                df_calculations_purlins["A_Vc_Rd"]
                * (df_calculations_purlins["Sterkteklasse"] / sqrt(3))
            )
            / M0
            / 1000
        ),
    )
    df_calculations_purlins.insert(
        66,
        "uc_VEd_Vc_Rd",
        (df_calculations_purlins["VEd"] / df_calculations_purlins["Vc_Rd"]),
    )
    df_calculations_purlins.insert(67, "controle_lijf_zonder_dwarsverstijvers", 0)
    df_calculations_purlins.insert(
        67,
        "uc_controle_lijf_zonder_dwarsverstijvers",
        (
            (df_calculations_purlins["hw"] / df_calculations_purlins["tw"])
            / ((72 * df_calculations_purlins["ε"]) / 1)
        ),
    )
    list_purlins_controle_dwarsverstijvers = []
    for index_1, row_1 in df_calculations_purlins.iterrows():
        if (row_1["hw"] / row_1["tw"]) > ((72 * row_1["ε"]) / 1):
            list_purlins_controle_dwarsverstijvers.append(
                "Controle nodig: H5 van EN1993-1-5"
            )
        else:
            list_purlins_controle_dwarsverstijvers.append("Geen controle nodig")
    df_calculations_purlins[
        "controle_lijf_zonder_dwarsverstijvers"
    ] = list_purlins_controle_dwarsverstijvers
    # """ TOETSING BUIGING EN DWARSKRACHT """
    df_calculations_purlins.insert(68, "ρ", 0)
    list_purlins_ρ = []
    for index_1, row_1 in df_calculations_purlins.iterrows():
        if row_1["uc_VEd_Vc_Rd"] <= 0.5:
            list_purlins_ρ.append(0)
        else:
            list_purlins_ρ.append(
                ((((2 * row_1["DZi/DZj"]) / row_1["n_profiles"]) / row_1["Vc_Rd"]) - 1)
                ** 2
            )
    df_calculations_purlins["ρ"] = list_purlins_ρ
    df_calculations_purlins.insert(
        69,
        "My_V_Rd",
        (
            (
                (
                    df_calculations_purlins["Wyy"]
                    - (
                        (
                            df_calculations_purlins["ρ"]
                            * df_calculations_purlins["Aw"] ** 2
                        )
                        / (4 * df_calculations_purlins["tw"])
                    )
                )
                * df_calculations_purlins["Sterkteklasse"]
                / M0
            )
            / 1000000
        ),
    )
    df_calculations_purlins.insert(70, "My_V_Rd_check", "")
    df_calculations_purlins.insert(
        70,
        "uc_My_V_Rd_check",
        (df_calculations_purlins["My_V_Rd"] / df_calculations_purlins["MRd"]),
    )
    list_purlins_My_V_Rd_check = []
    for index_1, row_1 in df_calculations_purlins.iterrows():
        if row_1["My_V_Rd"] <= row_1["MRd"]:
            list_purlins_My_V_Rd_check.append("Voldoet")
        else:
            list_purlins_My_V_Rd_check.append("Voldoet niet")
    df_calculations_purlins["My_V_Rd_check"] = list_purlins_My_V_Rd_check
    df_calculations_purlins.insert(
        71,
        "uc_MEd_My_V_Rd",
        (df_calculations_purlins["MEd"] / df_calculations_purlins["My_V_Rd"]),
    )
    df_calculations_purlins.insert(
        72,
        "a",
        (
            (
                df_calculations_purlins["A"]
                - (2 * df_calculations_purlins["b"] * df_calculations_purlins["tf"])
            )
            / df_calculations_purlins["A"]
        ),
    )
    df_calculations_purlins.insert(73, "check_a", "")
    list_purlins_check_a = []
    for row_1 in df_calculations_purlins["a"]:
        if row_1 <= 0.5:
            list_purlins_check_a.append("voldoet")
        else:
            list_purlins_check_a.append("voldoet niet")
    df_calculations_purlins["check_a"] = list_purlins_check_a
    df_calculations_purlins.insert(73, "uc_a", (df_calculations_purlins["a"] / 0.5))
    df_calculations_purlins.insert(
        74,
        "imperfectie",
        (
            (
                (
                    df_calculations_purlins["MEd"]
                    / df_calculations_purlins["MRd"]
                    * df_calculations_purlins["Sterkteklasse"]
                )
                + (
                    df_calculations_purlins["NEd_druk"]
                    / df_calculations_purlins["NRd"]
                    * df_calculations_purlins["Sterkteklasse"]
                )
            )
            / (
                2
                * df_calculations_purlins["MEd"]
                / df_calculations_purlins["MRd"]
                * df_calculations_purlins["Sterkteklasse"]
            )
        ),
    )
    df_calculations_purlins["imperfectie"] = df_calculations_purlins[
        "imperfectie"
    ].replace([nan], inf)
    list_purlins_imperfectie_klasse_1 = []
    for row_1 in df_calculations_purlins["imperfectie"]:
        if row_1 > 0.5:
            list_purlins_imperfectie_klasse_1.append(396)
        else:
            list_purlins_imperfectie_klasse_1.append(36)
    df_calculations_purlins.insert(75, "imperfectie_klasse_1", 0)
    df_calculations_purlins["imperfectie_klasse_1"] = list_purlins_imperfectie_klasse_1
    list_purlins_imperfectie_klasse_2 = []
    for row_1 in df_calculations_purlins["imperfectie"]:
        if row_1 > 0.5:
            list_purlins_imperfectie_klasse_2.append(456)
        else:
            list_purlins_imperfectie_klasse_2.append(41.5)
    df_calculations_purlins.insert(76, "imperfectie_klasse_2", 0)
    df_calculations_purlins["imperfectie_klasse_2"] = list_purlins_imperfectie_klasse_2

    list_purlins_imperfectie_klasse_ = []
    for index_1, row_1 in df_calculations_purlins.iterrows():
        if row_1["imperfectie"] > 0.5:
            list_purlins_imperfectie_klasse_.append(
                row_1["lijf c/t/ε"] * ((13 * row_1["imperfectie"]) - 1)
            )
        else:
            list_purlins_imperfectie_klasse_.append(
                row_1["lijf c/t/ε"] * row_1["imperfectie"]
            )
    df_calculations_purlins.insert(77, "imperfectie_klasse_", 0)
    df_calculations_purlins["imperfectie_klasse_"] = list_purlins_imperfectie_klasse_

    list_purlins_klasse_1 = []
    list_purlins_klasse_2 = []
    for index_1, row_1 in df_calculations_purlins.iterrows():
        if row_1["imperfectie_klasse_"] <= row_1["imperfectie_klasse_1"]:
            list_purlins_klasse_1.append(1)
        else:
            list_purlins_klasse_1.append(0)
        if row_1["imperfectie_klasse_"] <= row_1["imperfectie_klasse_2"]:
            list_purlins_klasse_2.append(1)
        else:
            list_purlins_klasse_2.append(0)
    df_calculations_purlins.insert(78, "klasse_1", 0)
    df_calculations_purlins["klasse_1"] = list_purlins_klasse_1
    df_calculations_purlins.insert(79, "klasse_2", 0)
    df_calculations_purlins["klasse_2"] = list_purlins_klasse_2

    list_purlins_drsn_kl_druk_buiging = []
    for index_1, row_1 in df_calculations_purlins.iterrows():
        if row_1["klasse_1"] + row_1["klasse_2"] == 2:
            list_purlins_drsn_kl_druk_buiging.append(1)
        if row_1["klasse_1"] + row_1["klasse_2"] == 1:
            list_purlins_drsn_kl_druk_buiging.append(2)
        if row_1["klasse_1"] + row_1["klasse_2"] == 0:
            list_purlins_drsn_kl_druk_buiging.append(3)
    df_calculations_purlins.insert(80, "drsn. kl. druk_buiging", 0)
    df_calculations_purlins[
        "drsn. kl. druk_buiging"
    ] = list_purlins_drsn_kl_druk_buiging

    list_purlins_MNy_RD = []
    for index_1, row_1 in df_calculations_purlins.iterrows():
        if (
            max(row_1["uc_NEd_trek_Nt_Rd"], row_1["uc_NEd_druk_Nc_Rd"]) <= 0.25
            and (
                max(row_1["NEd_trek"], row_1["NEd_druk"])
                * 1000
                / (row_1["hw"] * row_1["tw"] * row_1["Sterkteklasse"])
                / (2 * M0)
            )
            <= 1
        ):
            list_purlins_MNy_RD.append(row_1["MRd"])
        else:
            list_purlins_MNy_RD.append(
                row_1["Wyy"]
                * row_1["Sterkteklasse"]
                * (
                    (1 - max(row_1["uc_NEd_trek_Nt_Rd"], row_1["uc_NEd_druk_Nc_Rd"]))
                    / (1 - (0.5 * row_1["a"]))
                )
                / 1000000
            )

    df_calculations_purlins["MNy_Rd"] = list_purlins_MNy_RD
    df_calculations_purlins.insert(
        82,
        "uc_MEd_MNy_Rd",
        (df_calculations_purlins["MEd"] / df_calculations_purlins["MNy_Rd"]),
    )
    list_purlins_max_NEd = []
    for index_1, row_1 in df_calculations_purlins.iterrows():
        list_purlins_max_NEd.append(max(row_1["NEd_trek"], row_1["NEd_druk"]))
    df_calculations_purlins.insert(83, "max_NEd", 0)
    df_calculations_purlins["max_NEd"] = list_purlins_max_NEd

    df_calculations_purlins.insert(
        83,
        "uc_MEd_MNy_Rd_kl_3en4",
        (
            (
                df_calculations_purlins["max_NEd"]
                * 1000
                / (
                    df_calculations_purlins["A"]
                    * df_calculations_purlins["Sterkteklasse"]
                )
                / M0
            )
            + df_calculations_purlins["MEd"]
            * 1000000
            / (
                df_calculations_purlins["Wy_el"]
                * df_calculations_purlins["Sterkteklasse"]
            )
            / M0
        ),
    )
    list_purlins_uc_MEd_VEd_klasse = []
    for index_1, row_1 in df_calculations_purlins.iterrows():
        if row_1["drsn. kl. druk_buiging"] < 3:
            list_purlins_uc_MEd_VEd_klasse.append(row_1["uc_MEd_MNy_Rd"])
        if row_1["drsn. kl. druk_buiging"] > 2:
            list_purlins_uc_MEd_VEd_klasse.append(row_1["uc_MEd_MNy_Rd_kl_3en4"])

    df_calculations_purlins.insert(84, "uc_MEd_VEd_klasse_raw", 0)
    df_calculations_purlins["uc_MEd_VEd_klasse_raw"] = list_purlins_uc_MEd_VEd_klasse
    list_purlins_uc_MEd_VEd_klasse_def = []
    for index_1, row_1 in df_calculations_purlins.iterrows():
        if row_1["imperfectie"] == inf:
            list_purlins_uc_MEd_VEd_klasse_def.append(0)
        else:
            list_purlins_uc_MEd_VEd_klasse_def.append(row_1["uc_MEd_VEd_klasse_raw"])
    df_calculations_purlins.insert(85, "uc_MEd_VEd_klasse", 0)
    df_calculations_purlins["uc_MEd_VEd_klasse"] = list_purlins_uc_MEd_VEd_klasse_def
    # """TOETING BUIGING NORAAL EN DWARSKRACHT enkel voor droosnedeklasse 1 en 2, klasse 3 en 4 hoef niet getoetst te worden."""
    # TESTING NORMAL AND SHEAR FORCE for each droosnedeklass1 1 and 2. classes 3 and 4 do no need to be tested.
    list_purlins_reductie_check = []
    list_purlins_uc_reductie_check = []
    list_purlins_ρ_ = []
    for index_1, row_1 in df_calculations_purlins.iterrows():
        if row_1["uc_VEd_Vc_Rd"] <= 0.5:
            list_purlins_reductie_check.append("Geen reductie toepassen")
            list_purlins_uc_reductie_check.append(row_1["uc_VEd_Vc_Rd"] / 0.5)
            list_purlins_ρ_.append(0)
        else:
            list_purlins_reductie_check.append(
                "Reductie op combi buiging en normaalkracht"
            )
            list_purlins_uc_reductie_check.append(row_1["uc_VEd_Vc_Rd"] / 0.5)
            list_purlins_ρ_.append(
                ((((2 * row_1["VEd"]) / row_1["n_profiles"]) / row_1["Vc_Rd"]) - 1) ** 2
            )
    df_calculations_purlins.insert(86, "reductie_check", list_purlins_reductie_check)
    df_calculations_purlins.insert(
        86, "uc_reductie_check", list_purlins_uc_reductie_check
    )
    df_calculations_purlins.insert(87, "ρ_", list_purlins_ρ_)
    df_calculations_purlins.insert(
        88,
        "NVz_Rd",
        (
            (
                (
                    df_calculations_purlins["A"]
                    * df_calculations_purlins["Sterkteklasse"]
                )
                - (
                    df_calculations_purlins["ρ_"]
                    * df_calculations_purlins["Av"]
                    * df_calculations_purlins["Sterkteklasse"]
                )
            )
            / (M0 * 1000)
        ),
    )
    df_calculations_purlins.insert(
        89,
        "a1_",
        (
            (
                df_calculations_purlins["A"]
                - (2 * df_calculations_purlins["b"] * df_calculations_purlins["tf"])
            )
            / df_calculations_purlins["A"]
        ),
    )
    list_purlins_a1 = []
    for index_1, row_1 in df_calculations_purlins.iterrows():
        if row_1["a1_"] <= 0.5:
            list_purlins_a1.append(row_1["a1_"])
        else:
            list_purlins_a1.append(0.5)
    df_calculations_purlins.insert(90, "a1", list_purlins_a1)
    df_calculations_purlins.insert(
        91, "a2", (df_calculations_purlins["a1"] * (1 - df_calculations_purlins["ρ_"]))
    )
    df_calculations_purlins.insert(
        92,
        "MVy_Rd",
        (
            (
                (
                    df_calculations_purlins["Wyy"]
                    - (
                        (
                            df_calculations_purlins["ρ_"]
                            * df_calculations_purlins["Av"] ** 2
                        )
                        / (4 * df_calculations_purlins["tw"])
                    )
                )
                * df_calculations_purlins["Sterkteklasse"]
                / M0
            )
            / 1000000
        ),
    )
    df_calculations_purlins.insert(
        93,
        "uc_My_Ed_My_Vd_NEd_NVz_Rd_1en2",
        (
            (df_calculations_purlins["MEd"] / df_calculations_purlins["MVy_Rd"])
            + (
                (
                    (
                        df_calculations_purlins["max_NEd"]
                        / df_calculations_purlins["NVz_Rd"]
                    )
                    - (df_calculations_purlins["a2"] / 2)
                )
                / (1 - (df_calculations_purlins["a2"] / 2))
            )
        ),
    )
    list_purlins_uc_My_Ed_My_Vd_NEd_NVz_Rd = []
    for index_1, row_1 in df_calculations_purlins.iterrows():
        if row_1["drsn. kl. druk_buiging"] < 3:
            list_purlins_uc_My_Ed_My_Vd_NEd_NVz_Rd.append(
                row_1["uc_My_Ed_My_Vd_NEd_NVz_Rd_1en2"]
            )
        if row_1["drsn. kl. druk_buiging"] > 2:
            list_purlins_uc_My_Ed_My_Vd_NEd_NVz_Rd.append(0)

    df_calculations_purlins.insert(
        94, "uc_My_Ed_My_Vd_NEd_NVz_Rd", list_purlins_uc_My_Ed_My_Vd_NEd_NVz_Rd
    )

    #  L_BGT_wall is only for the BGT wall View tab. 1e6 factor to convert kN/m into N/mm
    df_calculations_purlins["L_BGT_wall"] = sqrt(
        df_calculations_purlins["Sterkteklasse"]
        * df_calculations_purlins["Wy_pl"]
        / (
            df_calculations_purlins["m_factor"]
            * df_calculations_purlins["BGT_stempelkracht"]
            * 1e6
        )
    )

    df_calculations_purlins["St."] = df_calculations_purlins["St."].astype(int)

    return df_calculations_purlins


def get_df_results_purlins(df_calculations_purlins: DataFrame) -> DataFrame:
    df_results_purlins = pd.DataFrame(data=None, columns=columns_results_purlins)
    for column_name in columns_results_purlins:
        if column_name in columns_calculations_purlins:
            df_results_purlins[column_name] = df_calculations_purlins[column_name]

    df_results_purlins = df_results_purlins.where(
        pd.notnull(df_calculations_purlins), 0
    )

    list_max_uc_purlins = []
    list_max_uc_purlins_UGT = []
    for index_1, row_1 in df_results_purlins.iterrows():
        list_max_uc_purlins.append(row_1["uc_MR_rep_ME_rep"])
        list_max_uc_purlins_UGT.append(
            max(
                row_1["uc_NEd_trek_Nt_Rd"],
                row_1["uc_NEd_druk_Nc_Rd"],
                row_1["uc_MEd_MRd"],
                row_1["uc_VEd_Vc_Rd"],
                row_1["uc_MEd_My_V_Rd"],
                row_1["uc_MEd_VEd_klasse"],
                row_1["uc_My_Ed_My_Vd_NEd_NVz_Rd"],
            )
        )

    df_results_purlins["uc_maatgevend"] = list_max_uc_purlins
    df_results_purlins["uc_maatgevend_UGT"] = list_max_uc_purlins_UGT

    # TODO, this loop builds a variable that is not used because row 19 is commented, remove entire block?
    list_name_max_uc_purlins = []
    for index_1, row_1 in df_results_purlins.iterrows():
        if row_1["uc_maatgevend_UGT"] == row_1["uc_NEd_trek_Nt_Rd"]:
            list_name_max_uc_purlins.append("Toetsing axiale trek")
        if row_1["uc_maatgevend_UGT"] == row_1["uc_NEd_druk_Nc_Rd"]:
            list_name_max_uc_purlins.append("Toetsing axiale druk")
        if row_1["uc_maatgevend_UGT"] == row_1["uc_MEd_MRd"]:
            list_name_max_uc_purlins.append("Toetsing buigend moment")
        if row_1["uc_maatgevend_UGT"] == row_1["uc_VEd_Vc_Rd"]:
            list_name_max_uc_purlins.append("Toetsing dwarskracht")
        if row_1["uc_maatgevend_UGT"] == row_1["uc_MEd_My_V_Rd"]:
            list_name_max_uc_purlins.append("Toetsing buiging en dwarskracht")
        if row_1["uc_maatgevend_UGT"] == row_1["uc_MEd_VEd_klasse"]:
            list_name_max_uc_purlins.append("Toetsing buiging en normaalkracht")
        if row_1["uc_maatgevend_UGT"] == row_1["uc_My_Ed_My_Vd_NEd_NVz_Rd"]:
            list_name_max_uc_purlins.append(
                "Toetsing buiging, dwarskracht en normaalkracht"
            )
    # df_results_purlins['toets_maatgevend'] = list_name_max_uc_purlins  ###################################### MISSCHIEN LATEN VERVALLEN. RISICO OP FOUTEN WANNEER ER 2 UC's HETZELFDE ZIJN

    list_results_uc_BGT = []
    for index_1, row_1 in df_results_purlins.iterrows():
        if row_1["uc_maatgevend_UGT"] <= 1:
            list_results_uc_BGT.append("Voldoet")
        else:
            list_results_uc_BGT.append("Voldoet niet")
    df_results_purlins["result"] = list_results_uc_BGT
    df_results_purlins["St."] = df_results_purlins["St."].astype(int)

    return df_results_purlins.sort_values(by=["St."])


def show_df(df_calculations_stamps):
    with pd.option_context(
        "display.max_rows", None, "display.max_columns", None
    ):  # more options can be specified also
        print(df_calculations_stamps)


def list_bars(df_results_purlins, index) -> Tuple[list, list]:
    if index == 0:
        max_uc_purlins_UGT = max(df_results_purlins["uc_maatgevend_UGT"])
        max_uc_purlins = max(df_results_purlins["uc_maatgevend"])
        df_bar_max_uc_UGT = df_results_purlins.loc[
            df_results_purlins["uc_maatgevend_UGT"] == max_uc_purlins_UGT
        ]
        df_bar_max_uc = df_results_purlins.loc[
            df_results_purlins["uc_maatgevend"] == max_uc_purlins
        ]

        list_bar_max_UGT: list = []
        for index_1, row_1 in df_bar_max_uc_UGT.iterrows():
            list_bar_max_UGT.append(row_1["Naam"])
        list_bar_max_UGT = str(list_bar_max_UGT)

        list_bar_max: list = []
        for index_1, row_1 in df_bar_max_uc.iterrows():
            list_bar_max.append(row_1["Naam"])
        list_bar_max = str(list_bar_max)
        return list_bar_max_UGT, list_bar_max
    return [], []


def get_df_nodes_new(df_nodes) -> DataFrame:
    """not used anywhere ?"""
    n_nodes = max(df_nodes["Knoop_1"].max(), df_nodes["Knoop_2"].max())
    dict_node_x, dict_node_z = get_nodes_dict_x_z(df_nodes)
    df_nodes_new = pd.DataFrame(data=None, columns=["Knoop", "X", "Z"])
    df_nodes_new["Knoop"] = arange(1, n_nodes + 1, 1)
    df_nodes_new["X"] = df_nodes_new["Knoop"].map(dict_node_x)
    df_nodes_new["Z"] = df_nodes_new["Knoop"].map(dict_node_z)
    return df_nodes_new


def get_nodes_dict_x_z(df_nodes) -> Tuple[dict, dict]:
    cols = []
    count = 1
    for column in df_nodes.columns:
        if column == "Knoop":
            cols.append(f"Knoop_{count}")
            count += 1
            continue
        cols.append(column)
    df_nodes.columns = cols

    cols = []
    count = 1
    for column in df_nodes.columns:
        if column == "X":
            cols.append(f"X_{count}")
            count += 1
            continue
        cols.append(column)
    df_nodes.columns = cols

    cols = []
    count = 1
    for column in df_nodes.columns:
        if column == "Z":
            cols.append(f"Z_{count}")
            count += 1
            continue
        cols.append(column)
    df_nodes.columns = cols

    df_nodes["Knoop_1"].replace("", 0, inplace=True)
    df_nodes["Knoop_1"] = df_nodes["Knoop_1"].astype(int)

    df_nodes["Knoop_2"].replace("", 0, inplace=True)
    df_nodes["Knoop_2"] = df_nodes["Knoop_2"].astype(int)

    node_list_x = []
    node_list_z = []
    df_coordinates_1 = pd.DataFrame(data=None, columns=["Knoop", "X", "Z"])
    df_coordinates_1["Knoop"] = df_nodes["Knoop_1"]
    df_coordinates_1["X"] = df_nodes["X_1"]
    df_coordinates_1["Z"] = df_nodes["Z_1"]
    df_coordinates_2 = pd.DataFrame(data=None, columns=["Knoop", "X", "Z"])
    df_coordinates_2["Knoop"] = df_nodes["Knoop_2"]
    df_coordinates_2["X"] = df_nodes["X_2"]
    df_coordinates_2["Z"] = df_nodes["Z_2"]
    for row_1, row_2, row_3 in zip(
        df_coordinates_1["X"], df_coordinates_1["Z"], df_coordinates_1["Knoop"]
    ):
        node_list_x.append({"Knoop": row_3, "X": row_1})
        node_list_z.append({"Knoop": row_3, "Z": row_2})
    for row_1, row_2, row_3 in zip(
        df_coordinates_2["X"], df_coordinates_2["Z"], df_coordinates_2["Knoop"]
    ):
        node_list_x.append({"Knoop": row_3, "X": row_1})
        node_list_z.append({"Knoop": row_3, "Z": row_2})
    dict_node_x = {
        node: x_coordinate
        for node, x_coordinate in zip(
            [row["Knoop"] for row in node_list_x], [row["X"] for row in node_list_x]
        )
    }
    dict_node_z = {
        node: z_coordinate
        for node, z_coordinate in zip(
            [row["Knoop"] for row in node_list_z], [row["Z"] for row in node_list_z]
        )
    }
    return dict_node_x, dict_node_z


def add_profile_parameters_to_df(df_to_be_iterated: DataFrame, string: str):
    df_table_profiles = get_profiles_table()

    df_table_profiles = df_table_profiles.rename(
        columns={
            "Wel": "Wy_el",
            "Wpl": "Wy_pl",
            "Wel-z": "Wz_el",
            "Wpl-z": "Wz_pl",
            "Izwakke as": "Iz",
            "kN/m": "G",
        }
    )
    dict_list_purlins_profile_variables = {
        "h": [],
        "b": [],
        "A": [],
        "Wy_el": [],
        "Wy_pl": [],
        "Wz_el": [],
        "Wz_pl": [],
        "tw": [],
        "tf": [],
        "r": [],
        "Iy": [],
        "Iz": [],
        "G": [],
    }

    df_table_profiles = df_table_profiles.set_index("Naam").to_dict("index")
    for index_1, row_1 in df_to_be_iterated.iterrows():
        profile_parameters = df_table_profiles[row_1[string]]
        for key, value in dict_list_purlins_profile_variables.items():
            value.append(profile_parameters[key])

    for key, value in dict_list_purlins_profile_variables.items():
        df_to_be_iterated[key] = value
        df_to_be_iterated[key] = df_to_be_iterated[key].astype(float)
    return None


def get_df_displacement(
    df_calculations_purlins, df_displacement_BGT: DataFrame
) -> DataFrame:
    # BEGIN VERPLAATSING
    list_purlin_beams = []  # voor toetsen gordingen op verplaatsing
    for index_1, row_1 in df_calculations_purlins.iterrows():
        if row_1["St."] not in list_purlin_beams:
            list_purlin_beams.append(row_1["St."])
    # list_beams = []       # voor toetsen gordingen, stempels en schoren op verplaatsing
    # # dict_displacement_x = []
    # # dict_displacement_z = []
    # for index_1, row in df_bars.iterrows():
    #     list_beams.append(row['St.'])
    list_max_displacement_z_lo = []
    list_min_displacement_z_lo = []
    df_displacement_BGT["Verpl_z_lo"] = df_displacement_BGT["Verpl_z_lo"].astype(float)
    for beam in list_purlin_beams:
        value_displacement = df_displacement_BGT.loc[df_displacement_BGT["St."] == beam]
        list_max_displacement_z_lo.append(
            {"St.": beam, "Max": value_displacement["Verpl_z_lo"].max()}
        )
        list_min_displacement_z_lo.append(
            {"St.": beam, "Min": value_displacement["Verpl_z_lo"].min()}
        )

    df_displacement = DataFrame(
        data=None, columns=["St.", "max_z", "min_z", "max_abs", "min_abs", "uc"]
    )
    df_displacement["St."] = list_purlin_beams
    dict_displacement_z_lo_max = {
        ID: value
        for ID, value in zip(
            [id["St."] for id in list_max_displacement_z_lo],
            [id["Max"] for id in list_max_displacement_z_lo],
        )
    }
    df_displacement["max_z"] = df_displacement["St."].map(dict_displacement_z_lo_max)
    dict_displacement_z_lo_min = {
        ID: value
        for ID, value in zip(
            [id["St."] for id in list_min_displacement_z_lo],
            [id["Min"] for id in list_min_displacement_z_lo],
        )
    }
    df_displacement["min_z"] = df_displacement["St."].map(dict_displacement_z_lo_min)
    df_displacement["max_abs"] = df_displacement["max_z"].abs()
    df_displacement["min_abs"] = df_displacement["min_z"].abs()
    list_uc_displacement = []
    for index_1, row_1 in df_displacement.iterrows():
        list_uc_displacement.append(max(row_1["max_abs"], row_1["min_abs"]))
    df_displacement["uc"] = list_uc_displacement
    # df_displacement['uc'] = round((df_displacement['uc'] / params.calculation.vervorming), 2)
    return df_displacement
