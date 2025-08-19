from itertools import chain
from pathlib import Path
from typing import List, Dict

from munch import Munch

from app.XMLupload.constants import stamp_failure
from viktor import File
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET


class XMLParser:
    def __init__(self, file: File):
        self.root = ET.fromstring(file.getvalue())

    @property
    def nodes(self):
        return [
            {
                "id": node.get("ID"),
                "x": float(node.get("X")),
                "z": float(node.get("Z")),
                "support_lsc_angle": float(node.get("SupportLCSAngle", 0)),
            }
            for node in self.root.find("Nodes")
        ]

    @property
    def bars(self):
        return [
            {
                "id": bar.get("ID"),
                "StartNodeID": bar.get("StartNodeID"),
                "EndNodeID": bar.get("EndNodeID"),
                "SectionID": bar.get("SectionID"),
                "ConnectionCodeStart": bar.get("ConnectionCodeStart"),
                "ConnectionCodeEnd": bar.get("ConnectionCodeEnd"),
            }
            for bar in self.root.find("Bars")
        ]

    def parse_input_file(self) -> dict:
        root = self.root

        materials = [
            {
                "material_id": material.get("ID"),
                "description": material.get("Description"),
                "material_type": material.get("MaterialType"),
            }
            for material in root.find("Materials")
        ]
        sections = [
            {
                "section_id": section.get("ID"),
                "description": section.get("Description"),
                "material_id": section.get("MaterialID"),
            }
            for section in root.find("Sections")
        ]

        fixedsupports = [
            {
                "ID": fixedsupport.get("ID"),
                "NodeID": fixedsupport.get("NodeID"),
                "DirectionXZR": fixedsupport.get("DirectionXZR"),
            }
            for fixedsupport in root.find("FixedSupports")
        ]

        springsupports = [
            {
                "ID": springsupport.get("ID"),
                "NodeID": springsupport.get("NodeID"),
                "Direction": springsupport.get("Direction"),
                "SpringConstant": springsupport.get("SpringConstant"),
                "SpringType": springsupport.get("SpringType"),
                "LowerLimit": springsupport.get("LowerLimit"),
                "UpperLimit": springsupport.get("UpperLimit"),
            }
            for springsupport in root.find("SpringSupports")
        ]

        beddings = [
            {
                "ID": bedding.get("ID"),
                "BarID": bedding.get("BarID"),
                "BeddingValue": bedding.get("BeddingValue"),
                "BeddingWidth": bedding.get("BeddingWidth"),
                "Side": bedding.get("Side"),
            }
            for bedding in root.find("Beddings")
        ]

        loadcases = [
            {
                "ID": loadcase.get("ID"),
                "description": loadcase.get("description"),
                "LoadCaseType": loadcase.get("LoadCaseType"),
            }
            for loadcase in root.find("LoadCases")
        ]

        barloads_UGT = [
            {
                "ID": barload_UGT.get("ID"),
                "BarID": barload_UGT.get("BarID"),
                "LoadCaseID": barload_UGT.get("LoadCaseID"),
                "LoadID": barload_UGT.get("LoadID"),
                "Type": barload_UGT.get("Type"),
                "LoadStart": barload_UGT.get("LoadStart"),
                "LoadEnd": barload_UGT.get("LoadEnd"),
                "DistanceStart": barload_UGT.get("DistanceStart"),
                "DistanceEnd": barload_UGT.get("DistanceEnd"),
            }
            for barload_UGT in root.find("BarLoads")
            if int(barload_UGT.get("LoadCaseID")) == 1
        ]

        barloads_BGT = [
            {
                "ID": barload_UGT.get("ID"),
                "BarID": barload_UGT.get("BarID"),
                "LoadCaseID": barload_UGT.get("LoadCaseID"),
                "LoadID": barload_UGT.get("LoadID"),
                "Type": barload_UGT.get("Type"),
                "LoadStart": barload_UGT.get("LoadStart"),
                "LoadEnd": barload_UGT.get("LoadEnd"),
                "DistanceStart": barload_UGT.get("DistanceStart"),
                "DistanceEnd": barload_UGT.get("DistanceEnd"),
            }
            for barload_UGT in root.find("BarLoads")
            if int(barload_UGT.get("LoadCaseID")) == 2
        ]

        load_combinations = [
            {
                "ID": load_combination.get("ID"),
                "description": load_combination.get("description"),
                "Type": load_combination.get("Type"),
            }
            for load_combination in root.find("LoadCombinations")
        ]

        load_combination_sets = [
            {
                "ID": load_combination_set.get("ID"),
                "LoadCombinationID": load_combination_set.get("LoadCombinationID"),
                "LoadCaseID": load_combination_set.get("LoadCaseID"),
                "IntensityType": load_combination_set.get("IntensityType"),
                "Factor": load_combination_set.get("Factor"),
            }
            for load_combination_set in root.find("LoadCombinationSets")
        ]

        # DICTIONARIES
        material_dict = {
            material["material_id"]: material["description"] for material in materials
        }
        profile_dict = {
            section["section_id"]: section["description"] for section in sections
        }
        bar_material_dict = {
            section["section_id"]: section["material_id"] for section in sections
        }

        result = {
            "general": {
                "geometry": {
                    "nodes": [
                        {
                            "id": node["id"],
                            "x": node["x"],
                            "z": node["z"],
                        }
                        for node in self.nodes
                    ]
                },
                "beams": {
                    "staven": [
                        {
                            "id": bar["id"],
                            "ki": bar["StartNodeID"],
                            "kj": bar["EndNodeID"],
                            "profiel": profile_dict[bar["SectionID"]],
                            "strength_class": material_dict[
                                bar_material_dict[bar["SectionID"]]
                            ],
                            "aansli": bar["ConnectionCodeStart"],
                            "aanslj": bar["ConnectionCodeEnd"],
                        }
                        for bar in self.bars
                    ]
                },
                "bedding": {
                    "staven": [
                        {
                            "ID": bedding["ID"],
                            "BarID": bedding["BarID"],
                            "BeddingValue": bedding["BeddingValue"],
                            "BeddingWidth": bedding["BeddingWidth"],
                            "Side": bedding["Side"],
                        }
                        for bedding in beddings
                    ]
                },
                "FixedSupports": {
                    "nodes": [
                        {
                            "ID": fixedsupport["ID"],
                            "NodeID": fixedsupport["NodeID"],
                            "DirectionXZR": fixedsupport["DirectionXZR"],
                        }
                        for fixedsupport in fixedsupports
                    ]
                },
                "SpringSupports": {
                    "nodes": [
                        {
                            "ID": springsupport["ID"],
                            "NodeID": springsupport["NodeID"],
                            "Direction": springsupport["Direction"],
                            "SpringConstant": springsupport["SpringConstant"],
                            "SpringType": springsupport["SpringType"],
                            "LowerLimit": springsupport["LowerLimit"],
                            "UpperLimit": springsupport["UpperLimit"],
                            # Get spring angle by finding angle of corresponding node
                            "support_lsc_angle": next(
                                node["support_lsc_angle"]
                                for node in self.nodes
                                if node["id"] == springsupport["NodeID"]
                            ),
                        }
                        for springsupport in springsupports
                    ]
                },
                "BarLoad_UGT": {
                    "staven": [
                        {
                            "ID": barload_UGT["ID"],
                            "BarID": barload_UGT["BarID"],
                            "Type": barload_UGT["Type"],
                            "LoadStart": barload_UGT["LoadStart"],
                            "LoadEnd": barload_UGT["LoadEnd"],
                            "DistanceStart": barload_UGT["DistanceStart"],
                            "DistanceEnd": barload_UGT["DistanceEnd"],
                        }
                        for barload_UGT in barloads_UGT
                    ]
                },
                "BarLoad_BGT": {
                    "staven": [
                        {
                            "ID": barload_BGT["ID"],
                            "BarID": barload_BGT["BarID"],
                            "Type": barload_BGT["Type"],
                            "LoadStart": barload_BGT["LoadStart"],
                            "LoadEnd": barload_BGT["LoadEnd"],
                            "DistanceStart": barload_BGT["DistanceStart"],
                            "DistanceEnd": barload_BGT["DistanceEnd"],
                        }
                        for barload_BGT in barloads_BGT
                    ]
                },
                "LoadCases": {
                    "loads": [
                        {
                            "ID": loadcase["ID"],
                            "description": loadcase["description"],
                            "LoadCaseType": loadcase["LoadCaseType"],
                        }
                        for loadcase in loadcases
                    ]
                },
            }
        }
        return result

    def set_length(self) -> dict:
        node_dict_x = {node["id"]: node["x"] for node in self.nodes}
        node_dict_z = {node["id"]: node["z"] for node in self.nodes}

        df_length_bars = pd.DataFrame(
            data=None,
            columns=["ID", "ki", "ki_x", "ki_z", "kj", "kj_x", "kj_z", "length"],
        )
        df_length_bars["ID"] = [key["id"] for key in self.bars]
        df_length_bars["ki"] = [key["StartNodeID"] for key in self.bars]
        df_length_bars["kj"] = [key["EndNodeID"] for key in self.bars]
        df_length_bars["ki_x"] = df_length_bars["ki"].map(node_dict_x)
        df_length_bars["ki_z"] = df_length_bars["ki"].map(node_dict_z)
        df_length_bars["kj_x"] = df_length_bars["kj"].map(node_dict_x)
        df_length_bars["kj_z"] = df_length_bars["kj"].map(node_dict_z)
        df_length_bars["length"] = round(
            np.sqrt(
                (
                    df_length_bars["kj_x"].astype(float)
                    - df_length_bars["ki_x"].astype(float)
                )
                ** 2
                + (
                    df_length_bars["kj_z"].astype(float)
                    - df_length_bars["ki_z"].astype(float)
                )
                ** 2
            ),
            3,
        )
        df_length_bars["length"] = df_length_bars["length"].astype(str)
        dict_bars_lengt_ = df_length_bars.set_index("ID").to_dict()

        dict_bars_length = dict_bars_lengt_["length"]
        result = self.parse_input_file()

        for bar in result["general"]["beams"]["staven"]:
            bar.update(
                {
                    "hoh": dict_bars_length[bar["id"]],
                }
            )

        return result

    def _update_xml_parameters(self, params: Munch, beam_table: List = None) -> ET:
        """Updates the .xml file"""
        root = self.root
        general_table = params.project_general.basics
        node_table = params.general.geometry.nodes
        # beam_table = params.general.beams.staven
        bedding_table = params.general.bedding.staven
        fixedsupport_table = params.general.FixedSupports.nodes
        spring_table = params.general.SpringSupports.nodes
        UGT_table = params.general.BarLoad_UGT.staven
        BGT_table = params.general.BarLoad_BGT.staven

        # """"Update the .mxl file BasicData - filename""""
        for parent in root.findall("BasicData"):
            for basic in parent.findall("Basic"):
                parent.remove(basic)

            new_basic = ET.SubElement(parent, "Basic")
            new_basic.set("FileVersion", "5.83")
            new_basic.set("Program", "twrmw")
            new_basic.set("ProgramVersion", "6.70")
            new_basic.set(
                "TemplateFileName",
                r"C:\TechnosoftWorkDir\template_20.0000-B Stempelframe.rww",
            )
            new_basic.set("XMLReadCode", "1")

            # """"Update the .mxl file GeneralData - filename""""

            general_data = []
            for general in root.find("GeneralData"):
                general_data.append(
                    {
                        "AlterationRejection": general.get("AlterationRejection"),
                        "CalculationType": general.get("CalculationType"),
                        "ExistingBuilding": general.get("ExistingBuilding"),
                        "PriorTo2003": general.get("PriorTo2003"),
                        "Standard": general.get("Standard"),
                        "Client": general.get("Client"),
                        "Date": general.get("Date"),
                        "Description": general.get("Description"),
                        "Dimensions": general.get("Dimensions"),
                        "Engineer": general.get("Engineer"),
                        "ProjectNr": general.get("ProjectNr"),
                    }
                )
            for parent in root.findall("GeneralData"):
                for general in parent.findall("General"):
                    general.set(
                        "File",
                        r"C:\TechnosoftWorkDir\template_20.0000-B Stempelframe.rww",
                    )

        # """"Update the .mxl file with nodes"""
        for parent in root.findall("Nodes"):
            for node in parent.findall("Node"):
                parent.remove(node)

        for parent in root.findall("Nodes"):
            for node in node_table:
                new_node = ET.SubElement(parent, "Node")
                new_node.set("ID", str(node["id"]))
                new_node.set("X", str(node["x"]))
                new_node.set("Z", str(node["z"]))

                # Get lsc angle from spring table entry with similar NodeID.
                # If corresponding NodeID is not found in spring table, angle is assumed to be zero
                try:
                    support_lsc_angle = next(
                        spring["support_lsc_angle"]
                        for spring in spring_table
                        if spring["NodeID"] == node["id"]
                    )
                except StopIteration as e:
                    support_lsc_angle = 0
                new_node.set("SupportLCSAngle", str(support_lsc_angle))

        #        """"Update the .mxl file with bars"""
        for parent in root.findall("Bars"):
            for bar in parent.findall("Bar"):
                parent.remove(bar)

        # Toekennen nieuwe Section ID's voor profielen
        prof_sterkte = []
        prof_sterkte_ = []
        prof_sterkte_combi = []
        barID = []
        for bars in beam_table:
            barID.append(bars.id)
            text_ = ["-".join((bars["profiel"], bars["strength_class"]))]
            prof_sterkte.append(text_)
        for i in prof_sterkte:
            for j in i:
                prof_sterkte_.append(j)

        for i in prof_sterkte_:
            if i not in prof_sterkte_combi:
                prof_sterkte_combi.append(i)

        n_profileID = np.arange(1, len(prof_sterkte_combi) + 1, 1)
        sectionID_dict = {
            profile: id for profile, id in zip(prof_sterkte_combi, n_profileID)
        }

        new_SectionID = []
        for bar in prof_sterkte_:
            new_SectionID.append(sectionID_dict[bar])

        # Invullen Bars in XML
        for parent in root.findall("Bars"):
            for bar, id in zip(beam_table, new_SectionID):
                new_bar = ET.SubElement(parent, "Bar")
                new_bar.set("ID", str(bar["id"]))
                new_bar.set("StartNodeID", str(bar["ki"]))
                new_bar.set("EndNodeID", str(bar["kj"]))
                new_bar.set("SectionID", str(id))
                new_bar.set("ConnectionCodeStart", str(bar["aansli"]))
                new_bar.set("ConnectionCodeEnd", str(bar["aanslj"]))

        #        """"Update the .mxl file with sections"""
        for parent in root.findall("Sections"):
            for section in parent.findall("Section"):
                parent.remove(section)

        new_section_description = []
        for bar in prof_sterkte_combi:
            section_profiles = bar.split("-")
            del section_profiles[-1]
            new_section_description.append(section_profiles)
        new_section_description = ["".join(ele) for ele in new_section_description]

        list_sterkteklasse = []
        for bar in prof_sterkte_combi:
            section_profiles = bar.split("-")
            del section_profiles[:1]
            list_sterkteklasse.append(section_profiles)
        list_sterkteklasse = ["".join(ele) for ele in list_sterkteklasse]

        materialID = []
        for i in list_sterkteklasse:
            if i not in materialID:
                materialID.append(i)

        n_materialID = np.arange(1, len(materialID) + 1, 1)
        materialID_dict = {sterkte: id for sterkte, id in zip(materialID, n_materialID)}

        new_section_materialID = []
        for sterkte in list_sterkteklasse:
            new_section_materialID.append(materialID_dict[sterkte])

        # Invullen sections in XML
        for parent in root.findall("Sections"):
            for sectionID, description, material_ID in zip(
                n_profileID, new_section_description, new_section_materialID
            ):
                new_section = ET.SubElement(parent, "Section")
                new_section.set("ID", str(sectionID))
                new_section.set("Description", str(description))
                new_section.set("MaterialID", str(material_ID))

        #        """"Update the .mxl file with materials"""
        for parent in root.findall("Materials"):
            for material in parent.findall("Material"):
                parent.remove(material)

        materialID_dict_2 = {
            id: sterkte for id, sterkte in zip(n_materialID, materialID)
        }

        new_material_description = []
        for material in n_materialID:
            new_material_description.append(materialID_dict_2[material])

        # Invullen materials in XML
        for parent in root.findall("Materials"):
            for id, description in zip(n_materialID, new_material_description):
                new_material = ET.SubElement(parent, "Material")
                new_material.set("ID", str(id))
                new_material.set("Description", str(description))
                new_material.set("MaterialType", "Steel")

        #        """"Update the .mxl file with beddings"""
        for parent in root.findall("Beddings"):
            for bedding in parent.findall("Bedding"):
                parent.remove(bedding)

        for parent in root.findall("Beddings"):
            for bedding in bedding_table:
                if all(bedding.values()):
                    new_bedding = ET.SubElement(parent, "Bedding")
                    new_bedding.set("ID", str(bedding["ID"]))
                    new_bedding.set("BarID", str(bedding["BarID"]))
                    new_bedding.set("BeddingValue", str(bedding["BeddingValue"]))
                    new_bedding.set("BeddingWidth", str(bedding["BeddingWidth"]))
                    new_bedding.set("Side", str(bedding["Side"]))

        #        """"Update the .mxl file with fixedsupports"""
        for parent in root.findall("FixedSupports"):
            for fixedsupport in parent.findall("FixedSupport"):
                parent.remove(fixedsupport)

        for parent in root.findall("FixedSupports"):
            for fixedsupport in fixedsupport_table:
                new_fixedsupport = ET.SubElement(parent, "FixedSupport")
                new_fixedsupport.set("ID", str(fixedsupport["ID"]))
                new_fixedsupport.set("NodeID", str(fixedsupport["NodeID"]))
                new_fixedsupport.set("DirectionXZR", str(fixedsupport["DirectionXZR"]))

        #        """"Update the .mxl file with springs"""
        for parent in root.findall("SpringSupports"):
            for spring in parent.findall("SpringSupport"):
                parent.remove(spring)

        for parent in root.findall("SpringSupports"):
            for spring in spring_table:
                new_springsupport = ET.SubElement(parent, "SpringSupport")
                new_springsupport.set("ID", str(spring["ID"]))
                new_springsupport.set("NodeID", str(spring["NodeID"]))
                new_springsupport.set("Direction", str(spring["Direction"]))
                new_springsupport.set("SpringConstant", str(spring["SpringConstant"]))
                new_springsupport.set("SpringType", str(spring["SpringType"]))
                new_springsupport.set("LowerLimit", str(spring["LowerLimit"]))
                new_springsupport.set("UpperLimit", str(spring["UpperLimit"]))

        #        """"Update the .mxl file with barloads"""
        for parent in root.findall("BarLoads"):
            for barload in parent.findall("BarLoad"):
                parent.remove(barload)

        UGT_load_id = []
        for id in UGT_table:
            UGT_load_id.append(id["ID"])
        len_UGT_load_id = np.arange(1, len(UGT_load_id) + 1, 1)

        BGT_load_id = []
        for id in BGT_table:
            BGT_load_id.append(id["ID"])
        len_BGT_load_id = np.arange(1, len(BGT_load_id) + 1, 1)

        # UGT
        for parent in root.findall("BarLoads"):
            for UGT, BGT, len_UGT in zip(UGT_table, BGT_table, len_UGT_load_id):
                new_barload = ET.SubElement(parent, "BarLoad")
                new_barload.set("ID", str(UGT["ID"]))
                new_barload.set("LoadCaseID", str("1"))
                new_barload.set("LoadID", str(len_UGT))
                new_barload.set("BarID", str(UGT["BarID"]))
                new_barload.set("Type", str(UGT["Type"]))
                new_barload.set("LoadStart", str(UGT["LoadStart"]))
                new_barload.set("LoadEnd", str(UGT["LoadEnd"]))
                new_barload.set("DistanceStart", str(UGT["DistanceStart"]))
                new_barload.set("DistanceEnd", str(UGT["DistanceEnd"]))
        # BGT
        for parent in root.findall("BarLoads"):
            for UGT, BGT, len_BGT in zip(UGT_table, BGT_table, len_BGT_load_id):
                new_barload = ET.SubElement(parent, "BarLoad")
                new_barload.set("ID", str(BGT["ID"]))
                new_barload.set("LoadCaseID", str("2"))
                new_barload.set("LoadID", str(len_BGT))
                new_barload.set("BarID", str(BGT["BarID"]))
                new_barload.set("Type", str(BGT["Type"]))
                new_barload.set("LoadStart", str(BGT["LoadStart"]))
                new_barload.set("LoadEnd", str(BGT["LoadEnd"]))
                new_barload.set("DistanceStart", str(BGT["DistanceStart"]))
                new_barload.set("DistanceEnd", str(BGT["DistanceEnd"]))

        ### Add extra Material with Young Modulus = 0 and assign the section with the stamp failure to this material
        number_of_materials = len(root.find("Materials"))

        id_ = None
        sections = []
        for section in root.find("Sections"):
            if section.get("Description") == stamp_failure:
                id_ = str(number_of_materials + 1)
                section.set("MaterialID", id_)
            sections.append(
                {
                    "ID": section.get("ID"),
                    "Description": section.get("Description"),
                    "MaterialID": section.get("MaterialID"),
                }
            )

        materials = []
        for material in root.find("Materials"):
            materials.append(
                {
                    "ID": material.get("ID"),
                    "Description": material.get("Description"),
                    "MaterialType": material.get("MaterialType"),
                }
            )

        if id_ is not None:
            sub_element = ET.SubElement(root.find("Materials"), "Material")
            sub_element.set("Description", "S235")
            sub_element.set("EmodulusX", "0.1")
            sub_element.set("ID", id_)
            sub_element.set("MaterialType", "Steel")

        return root
