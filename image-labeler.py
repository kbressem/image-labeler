#!/usr/bin/python3
# -*- coding: utf-8 -*-
# https://gist.github.com/acbetter/32c575803ec361c3e82064e60db4e3e0#file-qimageviewer-py

from PyQt5.QtCore import Qt, QRect, QMetaObject, QCoreApplication
from PyQt5.QtGui import QImage, QPixmap, QPalette, QPainter
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtWidgets import QLabel, QSizePolicy, QScrollArea, QMessageBox, QMainWindow, QMenu, QAction, qApp, QFileDialog, QComboBox, QWidget
import os

# for DICOM support
from pydicom import dcmread
from numpy import amax, uint8, rint
from PIL import Image


class QImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.printer = QPrinter()
        self.scaleFactor = 0.0

        self.imageLabel = QLabel()
        self.imageLabel.setBackgroundRole(QPalette.Base)
        self.imageLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)

        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        self.scrollArea.setVisible(False)

        self.autoSaveEnabled = True

        self.setCentralWidget(self.scrollArea)

        self.createActions()
        self.createMenus()

        self.setWindowTitle("Image Viewer")
        self.resize(1800, 1400)
        self.setupAnnotationArea()

    def setupAnnotationArea(self):

        self.loadPredefinedFindings()
        self.numberFindings = len(self.findings)

        # TODO: replace eval and exec with a dictionary
        for i in range(0, self.numberFindings):
            expr_name = 'self.finding_'+str(i)
            expr_construct = '=QComboBox(self)'
            expr_setGeometry = '.setGeometry(QRect(1410,'+str(i*30+10)+', 350, 25))'
            expr_setObjectName = '.setObjectName("finding_'+str(i)+'")'
            exec(expr_name+expr_construct)
            eval(expr_name+expr_setGeometry)
            eval(expr_name+expr_setObjectName)

        self.setupComboBoxes()

    def loadPredefinedFindings(self):
        self.findings = []
        with open("labels.config", "r") as f:
            for l in f.readlines():
                self.findings.append(l.replace("\n", "").split(","))

    def setupComboBoxes(self):
        for i in range(0, self.numberFindings):
            for f in self.findings[i]:
                expr = 'self.finding_'+str(i)+'.addItem(f)'
                eval(expr)

    def open(self):
        self.fileDir = QFileDialog.getExistingDirectory(self)
        self.fileNames = []
        self.imageExtensions = tuple([".png", ".jpeg", ".jpg", ".bmp", ".gif"])
        self.textExtensions = tuple([".txt"])
        for dirpath, subdirs, files in os.walk(self.fileDir):
            for f in files:
                if f.endswith(self.imageExtensions) or f.endswith(".dcm") or f.endswith(self.textExtensions):
                    self.fileNames.append(os.path.join(dirpath, f))
        self.fileNames.sort()
        self.imageNumber = 0
        self.show_image()
        self.loadFindings()
        self.nextAct.setEnabled(True)
        self.previousAct.setEnabled(True)
        self.saveAct.setEnabled(True)

    def show_image(self, adjustDicomWindow=False):
        self.fileName = self.fileNames[self.imageNumber]

        if self.fileName.endswith(self.textExtensions):
            with open(self.fileName, "r") as f:
                self.text = f.read()
            self.imageLabel.setText(self.text)
            self.imageLabel.setWordWrap(True)

        else:
            if self.fileName.endswith(self.imageExtensions):
                image = QImage(self.fileName)
                if image.isNull():
                    QMessageBox.information(self, "Image Viewer", "Cannot load %s." % fileName)
                    return
                self.imageLabel.setPixmap(QPixmap.fromImage(image))
            elif self.fileName.endswith(".dcm"):
                self.dicomLevelResetAct.setEnabled(True)
                for i in range(1,10):
                    expr = 'self.dicomLevelPreset'+str(i)+'Act.setEnabled(True)'
                    eval(expr)
                # very rudimentary DICOM support
                # TODO: (maybe) adujsting grey level values with mouse
                self.adjustDicomWindowLevel(adjustDicomWindow)
                self.imageLabel.setPixmap(QPixmap(".tmp.png"))

            # rescale very small images (CT, MRI), usually squared images. If not, then width
            # will likely be the smallest

        self.scaleFactor = 1.0
        self.scrollArea.setVisible(True)
        self.printAct.setEnabled(True)
        self.fitToWindowAct.setEnabled(True)
        self.updateActions()


        if not self.fitToWindowAct.isChecked():
            self.imageLabel.adjustSize()

        if self.fileName.endswith(self.imageExtensions) or self.fileName.endswith(".dcm"):
            if self.imageLabel.pixmap().width() < 1024:
                scaleFactor = 1024/self.imageLabel.pixmap().width()
                self.imageLabel.resize(scaleFactor * self.imageLabel.pixmap().size())
                # rescale very large images
            if self.imageLabel.pixmap().height() > 1024:
                scaleFactor = 1024/self.imageLabel.pixmap().height()
                self.imageLabel.resize(scaleFactor * self.imageLabel.pixmap().size())
            if self.imageLabel.pixmap().width() > 1024:
                scaleFactor = 1024/self.imageLabel.pixmap().width()
                self.imageLabel.resize(scaleFactor * self.imageLabel.pixmap().size())


    def adjustDicomWindowLevel(self, adjustDicomWindow=False):
        dicomFile = dcmread(self.fileName)
        arr = dicomFile.pixel_array
        if adjustDicomWindow:
            px_range = 255
            minval = self.wc - 0.5 - (self.ww - 1.0) / 2.0
            maxval = self.wc - 0.5 + (self.ww - 1.0) / 2.0

            min_mask = (minval >= arr)
            to_scale = (arr > minval) & (arr < maxval)
            max_mask = (arr >= maxval)

            if min_mask.any():
                arr[min_mask] = 0
            if to_scale.any():
                arr[to_scale] = ((arr[to_scale] - (self.wc - 0.5)) /
                                 (self.ww - 1.0) + 0.5) * px_range + 0
            if max_mask.any():
                arr[max_mask] = 255

            # round to next integer values and convert to unsigned int
            arr = rint(arr).astype(uint8)
            img = Image.fromarray((arr).astype(uint8))
        else:
            rescaleFactor = amax(arr)/256
            img = Image.fromarray((arr/rescaleFactor).astype(uint8))

        img.save(".tmp.png")

    def changeWindowLevel(self, preset, reset=False):
        presets=[]
        with open("windowlevel-presets.config", "r") as f:
            for l in f.readlines():
                presets.append(l.replace("\n", ""))

        if reset:
            self.show_image(adjustDicomWindow=False)
        else:
            self.wc = int(presets[preset].split(",")[0])
            self.ww = int(presets[preset].split(",")[1])
            self.show_image(adjustDicomWindow=True)

    def print_(self):
        dialog = QPrintDialog(self.printer, self)
        if dialog.exec_():
            painter = QPainter(self.printer)
            rect = painter.viewport()
            size = self.imageLabel.pixmap().size()
            size.scale(rect.size(), Qt.KeepAspectRatio)
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter.setWindow(self.imageLabel.pixmap().rect())
            painter.drawPixmap(0, 0, self.imageLabel.pixmap())

    def next(self):
        if self.autoSaveEnabled:
            self.writeFindings()
        else:
            pass
            # TODO: implement message box, asking for saving
            # how to make sure, the user really changed something and is not just scrolling though the images.
        if self.imageNumber < (len(self.fileNames)-1):
            self.imageNumber += 1
        else:
            self.imageNumber = 0
        self.show_image()
        self.restoreDefaults()
        self.loadFindings()

    def previous(self):
        if self.autoSaveEnabled:
            self.writeFindings()
        if self.imageNumber > 0:
            self.imageNumber -= 1
        else:
            self.imageNumber = (len(self.fileNames)-1)
        self.show_image()
        self.restoreDefaults()
        self.loadFindings()

    def writeFindings(self):
        saveName = os.path.splitext(self.fileName)[0]
        with open(saveName+"_annotation.csv", "w+") as a:
            for i in range(0, self.numberFindings):
                expr_name = 'self.finding_'+str(i)
                a.write(eval(expr_name+'.currentText()')+'\n')
        print("saved file at "+saveName+"_annotation.csv")

    def loadFindings(self):
        saveName = os.path.splitext(self.fileName)[0]+"_annotation.csv"
        if os.path.isfile(saveName):
            annotatedFinding=[]
            with open(saveName, "r") as a:
                for l in a.readlines():
                    annotatedFinding.append(l.replace("\n", ""))

            for i in range(0, self.numberFindings):
                expr_name = 'self.finding_'+str(i)
                eval(expr_name+'.setCurrentText(annotatedFinding['+str(i)+'])')

            print("loaded annotations from "+saveName)

    def restoreDefaults(self):
        for i in range(0, self.numberFindings):
            expr_name = 'self.finding_'+str(i)
            eval(expr_name+'.setCurrentIndex(0)')

    def toggleAutosave(self):
        if self.autoSaveEnabled:
            self.autoSaveEnabled = False
            self.toggleAutosaveAct.setText("Autosave Off")
        else:
            self.autoSaveEnabled = True
            self.toggleAutosaveAct.setText("Autosave On")

    def zoomIn(self):
        if not self.fileName.endswith(".txt"):
            self.scaleImage(1.25)

    def zoomOut(self):
        if not self.fileName.endswith(".txt"):
            self.scaleImage(0.8)

    def normalSize(self):
        if not self.fileName.endswith(".txt"):
            self.imageLabel.adjustSize()
            self.scaleFactor = 1.0

    def fitToWindow(self):
        fitToWindow = self.fitToWindowAct.isChecked()
        self.scrollArea.setWidgetResizable(fitToWindow)
        if not fitToWindow:
            self.normalSize()

        self.updateActions()

    def about(self):
        QMessageBox.about(self, "About Image Viewer",
                          "<p>The <b>Image Viewer</b> example shows how to combine "
                          "QLabel and QScrollArea to display an image. QLabel is "
                          "typically used for displaying text, but it can also display "
                          "an image. QScrollArea provides a scrolling view around "
                          "another widget. If the child widget exceeds the size of the "
                          "frame, QScrollArea automatically provides scroll bars.</p>"
                          "<p>The example demonstrates how QLabel's ability to scale "
                          "its contents (QLabel.scaledContents), and QScrollArea's "
                          "ability to automatically resize its contents "
                          "(QScrollArea.widgetResizable), can be used to implement "
                          "zooming and scaling features.</p>"
                          "<p>In addition the example shows how to use QPainter to "
                          "print an image.</p>")

    def createActions(self):
        self.openAct = QAction("&Open...", self, shortcut="Ctrl+O", triggered=self.open)
        self.printAct = QAction("&Print...", self, shortcut="Ctrl+P", enabled=False, triggered=self.print_)
        self.saveAct = QAction("Save Annotations", self, shortcut="Ctrl+S", enabled=False, triggered=self.writeFindings)
        self.toggleAutosaveAct = QAction("Autosave On", self, shortcut="Ctrl+A", enabled=True, triggered=self.toggleAutosave)

        self.exitAct = QAction("E&xit", self, shortcut="Ctrl+Q", triggered=self.close)
        self.zoomInAct = QAction("Zoom &In (25%)", self, shortcut="Ctrl++", enabled=False, triggered=self.zoomIn)
        self.zoomOutAct = QAction("Zoom &Out (25%)", self, shortcut="Ctrl+-", enabled=False, triggered=self.zoomOut)
        self.normalSizeAct = QAction("&Normal Size", self, shortcut="Ctrl+N", enabled=False, triggered=self.normalSize)
        self.nextAct = QAction("Ne&xt image", self, shortcut=Qt.Key_Right, enabled=False, triggered=self.next)
        self.previousAct = QAction("Previous Image", self, shortcut=Qt.Key_Left, enabled=False, triggered=self.previous)

        self.fitToWindowAct = QAction("&Fit to Window", self, enabled=False, checkable=True, shortcut="Ctrl+F",
                                      triggered=self.fitToWindow)
        self.aboutAct = QAction("&About", self, triggered=self.about)
        self.aboutQtAct = QAction("About &Qt", self, triggered=qApp.aboutQt)

        self.dicomLevelResetAct = QAction("Reset Window Level", self, shortcut="Ctrl+0", enabled=False,
                                            triggered=lambda: self.changeWindowLevel(preset = 0, reset = True))

        self.dicomLevelPreset1Act = QAction("Window Level Preset 1", self, shortcut="Ctrl+1", enabled=False, triggered=lambda: self.changeWindowLevel(preset = 1))
        self.dicomLevelPreset2Act = QAction("Window Level Preset 2", self, shortcut="Ctrl+2", enabled=False, triggered=lambda: self.changeWindowLevel(preset = 2))
        self.dicomLevelPreset3Act = QAction("Window Level Preset 3", self, shortcut="Ctrl+3", enabled=False, triggered=lambda: self.changeWindowLevel(preset = 3))
        self.dicomLevelPreset4Act = QAction("Window Level Preset 4", self, shortcut="Ctrl+4", enabled=False, triggered=lambda: self.changeWindowLevel(preset = 4))
        self.dicomLevelPreset5Act = QAction("Window Level Preset 5", self, shortcut="Ctrl+5", enabled=False, triggered=lambda: self.changeWindowLevel(preset = 5))
        self.dicomLevelPreset6Act = QAction("Window Level Preset 6", self, shortcut="Ctrl+6", enabled=False, triggered=lambda: self.changeWindowLevel(preset = 6))
        self.dicomLevelPreset7Act = QAction("Window Level Preset 7", self, shortcut="Ctrl+7", enabled=False, triggered=lambda: self.changeWindowLevel(preset = 7))
        self.dicomLevelPreset8Act = QAction("Window Level Preset 8", self, shortcut="Ctrl+8", enabled=False, triggered=lambda: self.changeWindowLevel(preset = 8))
        self.dicomLevelPreset9Act = QAction("Window Level Preset 9", self, shortcut="Ctrl+9", enabled=False, triggered=lambda: self.changeWindowLevel(preset = 9))

    def createMenus(self):
        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.printAct)
        self.fileMenu.addAction(self.saveAct)
        self.fileMenu.addAction(self.toggleAutosaveAct)

        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QMenu("&View", self)
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addAction(self.normalSizeAct)
        self.viewMenu.addAction(self.nextAct)
        self.viewMenu.addAction(self.previousAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.fitToWindowAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.dicomLevelResetAct)
        for i in range(1,10):
            expr = 'self.viewMenu.addAction(self.dicomLevelPreset'+str(i)+'Act)'
            eval(expr)
        self.viewMenu.addSeparator()



        self.helpMenu = QMenu("&Help", self)
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.helpMenu)

    def updateActions(self):
        self.zoomInAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.zoomOutAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.normalSizeAct.setEnabled(not self.fitToWindowAct.isChecked())

    def scaleImage(self, factor):
        self.scaleFactor *= factor
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())

        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)

        self.zoomInAct.setEnabled(self.scaleFactor < 3.0)
        self.zoomOutAct.setEnabled(self.scaleFactor > 0.333)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                               + ((factor - 1) * scrollBar.pageStep() / 2)))

    def closeEvent(self, event):
        if hasattr(self, 'fileDir'):
            close = QMessageBox()
            close.setText("Annotations are currently stored as mutliple text files."+
                          "Shall they be gathered and stored into a single CSV-file? \n\n"+
                          "This may take some time and the program might appear unresponsive.")
            close.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            close = close.exec()

            if close == QMessageBox.Yes:
                import pandas as pd
                annotationFiles = []
                annotations = []
                for dirpath, subdirs, files in os.walk(self.fileDir):
                    for f in files:
                        if f.endswith("_annotation.csv"):
                            annotationFiles.append(os.path.join(dirpath, f))
                for a in annotationFiles:
                    with open(a, "r") as f:
                        annotations.append([sub.replace("\n", "") for sub in f.readlines()])

                df = pd.DataFrame(annotations)
                df.insert(0, 'fileNames', annotationFiles)
                df.to_csv("annotations.csv")

        try:
            os.remove(".tmp.png")
        except:
            pass
        event.accept()


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    imageViewer = QImageViewer()

    imageViewer.show()

    sys.exit(app.exec_())
