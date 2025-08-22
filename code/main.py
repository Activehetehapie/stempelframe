import sys
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
        for table in self.tables:
            self.ui.TableLists.addItem(table[0])

    def Selectionchanged(self, index):
        self.ui.TableData.clearContents()
        self.ui.TableData.setRowCount(0)

        for table in self.tables:
            if table[0] == self.ui.TableLists.itemText(index):
                headers = table[1]
                data = table[2]

                self.ui.TableData.setColumnCount(len(headers))
                self.ui.TableData.setHorizontalHeaderLabels([str(h) for h in headers])
                self.ui.TableData.setRowCount(len(data))

                for row_idx, datarow in enumerate(data):
                    for col_idx, item in enumerate(datarow):
                        cell = QTableWidgetItem(str(item))
                        self.ui.TableData.setItem(row_idx, col_idx, cell)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = Interface()
    form.show()
    sys.exit(app.exec_())