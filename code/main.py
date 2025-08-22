import sys
import numpy as np
from interface import Ui_Interface
import parsefile

from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QTableWidgetItem

class Interface(QMainWindow):
    def __init__(self, *args):
        super().__init__()
        self.ui = Ui_Interface()
        self.ui.setupUi(self)
        self.setWindowTitle("Stempelframe")

        self.ui.ProcessFile.setDisabled(True)
        self.ui.ExtractKnopen.setDisabled(True)
        self.ui.SearchFile.clicked.connect(self.Searchfile)
        self.ui.ProcessFile.clicked.connect(self.Processfile)
        self.ui.TableLists.currentIndexChanged.connect(self.Selectionchanged)
        self.ui.ExtractKnopen.clicked.connect(self.Extractknopen)

        self.dataframes = {}
        self.tables = []

    def Searchfile(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            self.ui.SelectedFile.setText(file_path)
            self.ui.ProcessFile.setEnabled(True)

    def Processfile(self):
        self.parseddata, self.tables = parsefile.parsefile(self.ui.SelectedFile.text())
        self.ui.TableLists.clear()
        self.ui.ExtractKnopen.setEnabled(True)
        for table in self.tables:
            self.ui.TableLists.addItem(table[0])

    def Selectionchanged(self, index):
        self.ui.TableData.clearContents()
        self.ui.TableData.setRowCount(0)

        for table in self.tables:
            if table[0] == self.ui.TableLists.itemText(index):
                headers = table[1]
                data = table[2]
                print(len(headers))

                self.ui.TableData.setColumnCount(len(headers))
                self.ui.TableData.setHorizontalHeaderLabels([str(h) for h in headers])
                self.ui.TableData.setRowCount(len(data))

                for row_idx, datarow in enumerate(data):
                    for col_idx, item in enumerate(datarow):
                        cell = QTableWidgetItem(str(item))
                        self.ui.TableData.setItem(row_idx, col_idx, cell)

    def Extractknopen(self):
        self.Generateknopenset()
        self.getprof_len()
        self.getquality()
        self.getforce()
        self.calculateangles()

        name = "a name"
        existing_items = [self.ui.TableLists.itemText(i) for i in range(self.ui.TableLists.count())]
        if name not in existing_items:
            self.ui.TableLists.addItem(name)
            self.tables.append([name, self.knopentable[:1][0], self.knopentable[1:]])
        self.ui.TableLists.setCurrentText(name)



    def calculateangles(self):
        for table in self.tables:
            if table[0] == "STAVEN":
                for knoop in self.knopentable[1:]:
                    for item in table[2]:
                        if item[0] == knoop[0]:
                            startknoop = item[1]
                            eindknoop = item[2]
                            angle1 = self.Findshortestangle(startknoop, eindknoop)
                            angle2 = self.Findshortestangle(eindknoop, startknoop)
                            knoop[5] = angle1
                            knoop[6] = angle2
                continue

    def Findshortestangle(self, startknoop, eindknoop):
        linkknopen = [startknoop]
        for table in self.tables:
            if table[0] == "STAVEN":
                for item in table[2]:
                    if "H" in item[3]:
                        if item[1] == startknoop:
                            linkknopen.append(item[2])
                        elif item[2] == startknoop:
                            linkknopen.append(item[1])
        return self.Getcoordinates(linkknopen, eindknoop)

    def Getcoordinates(self, linkknopen, eindknoop):
        for table in self.tables:
            if table[0] == "KNOPEN":
                for item in table[2]:
                    for num, knoop in enumerate(linkknopen):
                        if item[0] == knoop:
                            linkknopen[num] = [item[1], item[2]]
                            continue
                        if item[0] == eindknoop:
                            eindknoop = [item[1], item[2]]
        angle_list = []
        for knoop in linkknopen[1:]:
            angle_list.append(self.angle_at_point(linkknopen[0], knoop, eindknoop))

        return float(round(self.get_smallest_angle(angle_list), 1))

    def get_smallest_angle(self, angle_list):
        if len(angle_list) == 2:
            if angle_list[0] + angle_list[1] > 90:
                return 180 - max(angle_list)
            else:
                return min(angle_list)
        else:
            exit(0)

    def angle_at_point(self, B, A, C):
        BA = [A[0] - B[0], A[1] - B[1]]
        BC = [C[0] - B[0], C[1] - B[1]]
        return self.angle_between_vectors(BA, BC)

    def angle_between_vectors(self, v1, v2):
        v1 = np.array(v1)
        v2 = np.array(v2)
        dot_product = np.dot(v1, v2)
        norm_product = np.linalg.norm(v1) * np.linalg.norm(v2)
        angle_rad = np.arccos(dot_product / norm_product)
        angle_deg = np.degrees(angle_rad)
        return angle_deg

    def getforce(self):
        for knoop in self.knopentable:
            for item in self.knopenset:
                if knoop[0] == item[0]:
                    if item[2] == 0:
                        knoop[7] = item[1]
                    else:
                        knoop[8] = item[1]
                    continue

    def getquality(self):
        for table in self.tables:
            if table[0] == "PROFIELEN [mm]":
                for knoop in self.knopentable:
                    for item in table[2][1:]:
                        if knoop[1] in item[1] and knoop[2] in item[1]:
                            knoop[3] = item[2].split(':')[1]
                            continue

    def getprof_len(self):
        self.knopenlist = []
        self.knopentable = [['Nr', chr(216),  'w', "st. kwal.", "Lengte", "Hoek 1", "Hoek 2", "UGT: Sterkte", "BGT: Vervorming"]]
        for item in self.knopenset:
            if item[0] not in self.knopenlist:
                self.knopenlist.append(item[0])
        for table in self.tables:
            if table[0] == "STAVEN":
                for staaf in table[2]:
                    if staaf[0] in self.knopenlist:
                        profiel = staaf[3].split('B')[1].split('/')
                        lengte = float(staaf[6])
                        print(profiel[0])
                        self.knopentable.append([staaf[0], profiel[0], profiel[1], 0, lengte, 0, 0, 0, 0])

    def Generateknopenset(self):
        self.knopenset = set()
        Krachttable = ["STAAFKRACHTEN  B.C:1 Sterkte", "STAAFKRACHTEN  B.C:2 Vervorming"]
        for table in self.tables:
            if table[0] in Krachttable:
                for item in table[2]:
                    if not item[2] and not item[4] and not item[5] and item [3]:
                        if "Sterkte" in table[0]:
                            knoop = (item[0], item[3], 0)
                        else:
                            knoop = (item[0], item[3], 1)
                        self.knopenset.add(knoop)
        print(self.knopenset)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = Interface()
    form.show()
    sys.exit(app.exec_())