import itertools
import re
from string import ascii_uppercase
from typing import Tuple

from munch import Munch
from pandas import DataFrame

from viktor import UserError


def get_diameter_from_profile_name(profile_name: str) -> float:
    """The profile structure is: 2:B508/12.5. This functions returns the diameter as a float: 508"""
    splitted_name = re.split("[, :/]+", profile_name)[1]
    return int(re.sub("\D", "", splitted_name[1:]))


def determine_type_strut(df_preface_forces: DataFrame, strut_id: int) -> str:
    """Determine the type of the strut provided by strut_id,
    stempel: has a angle 90 with an adjacent beam
    schoor: otherwise"""
    angles_list = []
    for _, row in df_preface_forces.iterrows():
        if int(row["s_aansl_St."]) == strut_id:
            angles_list.append(row["[°]"])
    if 90 in angles_list:
        return "stempel"
    else:
        return "schoor"


def strut_profile_from_strut_id(params: Munch, strut_id: int) -> str:
    for beam in params.general.beams.staven:
        if int(beam.id) == int(strut_id):
            return beam.profiel
    raise UserError(f"No beam with id {strut_id}")


def iter_all_strings():
    """Iterate through the alphabet a,b,c ...z, aa,ab,ac, ... zz, aaa. Infinitely. The generator has to be stopped
    when used"""
    for size in itertools.count(1):
        for s in itertools.product(ascii_uppercase, repeat=size):
            yield "".join(s)


def get_list_columns_letters(nb_columns: int, start: int = 1):
    letters_list = []
    for index, letter in enumerate(iter_all_strings()):
        letters_list.append(letter)
        if index == nb_columns:
            break
    return letters_list[start:]


def get_strut_angles(
    df_calculations_preface_force: DataFrame, strut_id: int
) -> Tuple[float, float]:
    """Based ont the Dataframe of preface force calculations, this function returns the angles on the A and B sides for
    the strut `strut_id`.
    A side is the node of the strut with lowest id
    B side is the node of the strut with highest id

    Remark/to do: Very ugly function, needs refactoring and decoupling of the calculation angles from this df.
    """
    angles_and_nodes_list = []
    nodes_list = []

    for _, row in df_calculations_preface_force.iterrows():
        if row["s_aansl_St."] == strut_id:
            temp_dict = {}
            temp_dict["node"] = int(row["Kn. Pos."])
            temp_dict["angle"] = float(row["[°]"])
            if int(temp_dict["angle"]) != 90:
                angles_and_nodes_list.append(temp_dict)
                nodes_list.append(int(row["Kn. Pos."]))

    if len(nodes_list) == 0:  # in that case, the only calculated angles are 90 degrees
        return 90, 90

    id_node_A = min(set(nodes_list))
    id_node_B = max(set(nodes_list))

    angle_A, angle_B = 360, 360  # Initializing values
    for row in angles_and_nodes_list:
        if row["node"] == id_node_A:
            angle_A = row["angle"] if row["angle"] < angle_A else angle_A
        if row["node"] == id_node_B:
            angle_B = row["angle"] if row["angle"] < angle_B else angle_B

    return angle_A, angle_B
