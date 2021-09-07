# This Python file uses the following encoding: utf-8
import sys
import pathlib

from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QInputDialog
from PySide6.QtCore import QFile, Slot, QDir
from PySide6.QtGui import QPalette, QColor, QColorConstants
from form import Ui_MainWindow
from html_delegate import HTMLDelegate
from bs4 import BeautifulSoup
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s: %(message)s'
)


class Risicompare(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(Risicompare, self).__init__()
        self.setupUi(self)

        # Connect
        self.identifierList.setItemDelegate(HTMLDelegate())
        self.bulkList.setItemDelegate(HTMLDelegate())
        self.upButton.clicked.connect(self.moveUp)
        self.downButton.clicked.connect(self.moveDown)
        self.leftButton.clicked.connect(self.moveLeft)
        self.rightButton.clicked.connect(self.moveRight)
        self.outputButton.clicked.connect(self.filePickerSave)
        self.htmlButton.clicked.connect(self.produceHTML)
        self.quitButton.triggered.connect(self.close)
        self.helpButton.triggered.connect(self.help)
        self.bulkFileButton.triggered.connect(lambda :self.filePickerOpen(True))
        self.identifierFileButton.triggered.connect(lambda: self.filePickerOpen(False))
        self.showImagesButton.triggered.connect(self.showImages)
        self.numParagraphButton.triggered.connect(self.setParagraphNumber)

        # Variables
        self.output_file = ""
        self.bulk_file = ""
        self.identifier_file = ""
        self.show_images = False
        self.part_order = dict()
        self.paragraphs = 3

        # ListView Cache delegate
        # See https://doc.qt.io/qt-6/qml-qtquick-listview.html#highlightMoveVelocity-prop
        self.identifierList.cacheBuffer = 10000
        self.bulkList.cacheBuffer = 10000


    @Slot()
    def moveUp(self):
        currentRow = self.identifierList.currentRow()
        currentItem = self.identifierList.takeItem(currentRow)
        self.identifierList.insertItem(currentRow - 1, currentItem)
        self.identifierList.setCurrentRow(currentRow - 1)


    @Slot()
    def moveDown(self):
        currentRow = self.identifierList.currentRow()
        currentItem = self.identifierList.takeItem(currentRow)
        self.identifierList.insertItem(currentRow + 1, currentItem)
        self.identifierList.setCurrentRow(currentRow + 1)


    @Slot()
    def moveLeft(self):
        currentRow = self.identifierList.currentRow()
        currentRowBulk = self.bulkList.currentRow()
        currentItem = self.identifierList.takeItem(currentRow)
        self.bulkList.insertItem(currentRowBulk + 1, currentItem)
        self.bulkList.setCurrentRow(currentRowBulk + 1)


    @Slot()
    def moveRight(self):
        currentRow = self.bulkList.currentRow()
        currentItem = self.bulkList.takeItem(currentRow)
        self.identifierList.insertItem(currentRow + 1, currentItem)
        self.identifierList.setCurrentRow(currentRow + 1)


    @Slot()
    def filePickerSave(self):
        fileName = QFileDialog.getSaveFileName(
                self,
                "Save html file",
                QDir.home().toNativeSeparators(QDir.home().path()),
                "HTML Files (*.html)"
        )
        self.output_file = fileName[0]


    @Slot(bool)
    def filePickerOpen(self, bulk):
        fileName = QFileDialog.getOpenFileName(
                self,
                "Open html file",
                QDir.home().toNativeSeparators(QDir.home().path()),
                "HTML Files (*.html)"
        )
        if bulk:
                self.bulk_file = fileName[0]
                if self.bulk_file == "":
                    return
                self.read_file(self.bulk_file, True)
        else:
                self.identifier_file = fileName[0]
                if self.identifier_file == "":
                    return
                self.read_file(self.identifier_file, False)



    @Slot()
    def read_file(self, file, bulk):
        html_list = []
        with open(file, "r") as f:
            for element in f:
                html_list.append(element)
        html = "".join(html_list)
        soup = BeautifulSoup(html, features="lxml")
        div = soup.select("div")
        # We remove some paragraph here to not
        # slow down the Delegate.
        for count , d in enumerate(div):
            p = d.select("p")
            self.part_order[count] = [div[count].decode()]
            for p in p[self.paragraphs:]:
                p.decompose()
        # The image rendering is also depressingly slow
        if not self.show_images:
            for element in div:
                for img in element.select("img"):
                    try:
                        img.attrs["src"] = ""
                    except AttributeError as e:
                        continue
        # We add the removed part into a dictionnary for
        # a lookup when writing to HTML.
        for count, element in enumerate(div):
            self.part_order[count].append(element.decode())
        if bulk:
            if self.bulkList.count() != 0:
                self.bulkList.clear()
            for element in div:
                self.bulkList.addItem(element.decode())
        else:
            if self.identifierList.count() != 0:
                self.identifierList.clear()
            for element in div:
                self.identifierList.addItem(element.decode())


    @Slot()
    def produceHTML(self):
        item_count = self.identifierList.count()
        html_risitas = []
        # We match the items html with the one in the dictionnary
        # to have a full html text and in the items order
        for element in range(item_count):
            item_to_compare = self.identifierList.item(element).text()
            for k, v in self.part_order.items():
                if item_to_compare == v[1] and item_to_compare not in html_risitas:
                    logging.info(f"The key is {k}")
                    logging.info(f"The value to compare to is '{v[1]}'")
                    logging.info(f"The element being compared is '{item_to_compare}'")
                    html_risitas.append(v[0])
                    break
        if self.output_file == "":
                msgBox = QMessageBox(icon=QMessageBox.Critical)
                msgBox.setText(f"No output file has been set!")
                msgBox.exec()
                return
        with open(self.output_file, "w") as f:
            html = (
                """<!DOCTYPE html>
                <html lang='fr'>
                <head>
                <meta charset='UTF-8'>
                <meta name='viewport' content='width=device-width, initial-scale=1.0'>
                <title>Risitas</title>
                </head>
                <body>"""
             )
            f.write(html)
            #for element in range(item_count):
            #    f.write(self.identifierList.item(element).text() + "\n")
            for element in html_risitas:
                f.write(element + "\n")
            html = (
                """</body>
                </html>"""
                )
            f.write(html)
        msgBox = QMessageBox(icon=QMessageBox.Information)
        msgBox.setText(f"The file has been written to {self.output_file}")
        msgBox.exec()



    @Slot()
    def showImages(self):
        checked = self.showImagesButton.isChecked()
        if checked:
            self.show_images = True
        else:
            self.show_images = False


    @Slot()
    def help(self):
        msgBox = QMessageBox(icon=QMessageBox.Information)
        msgBox.setText('''Scenario 1 : One chapter is missing in the identifier approach, go to left window -> select missing item
and click/press "move the item to the right button", then put the item in the right position by repeatingly pressing
the "down/up item button" for the right qlistwidget

Scenario 2: There are some duplicates in the identifier approach -> select the duplicates and click/press
the "move the item to the left button" to move them to the left QListWidget

Scenario 3: Some chapters in the identifier windows are not in the correct order -> move the items with the
move up/down buttons''')
        msgBox.exec()


    @Slot()
    def setParagraphNumber(self):
        i, ok = QInputDialog().getInt(self, "Number of paragraphs window",
                                 "Number of paragraphs to show:", 0, 0, 100, 1)
        if ok:
            self.paragraphs = i


if __name__ == "__main__":
    app = QApplication([])
    app.setStyle('Fusion')
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, QColor("white"))
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, QColor("black"))
    palette.setColor(QPalette.ToolTipText, QColor("white"))
    palette.setColor(QPalette.Text, QColor("white"))
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, QColor("white"))
    palette.setColor(QPalette.BrightText, QColor("red"))
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, QColor("black"))
    app.setPalette(palette)
    widget = Risicompare()
    widget.show()
    sys.exit(app.exec())
