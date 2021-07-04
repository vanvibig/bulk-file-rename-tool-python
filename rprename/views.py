from collections import deque
from pathlib import Path

from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QFileDialog, QWidget

from .rename import Renamer
from .ui.window import Ui_Window

FILTERS = ";;".join(
    (
        "PNG Files (*.png)",
        "JPEG Files (*.jpeg)",
        "JPG Files (*.jpg)",
        "GIF Files (*.gif)",
        "Text Files (*.txt)",
        "Python Files (*.py)",
    )
)


class Window(QWidget, Ui_Window):
    def __init__(self):
        super().__init__()
        self._files = deque()
        self._filesCount = len(self._files)
        self._setupUI()
        self._connectSignalsSlots()

    def _setupUI(self):
        self.setupUi(self)
        self._updateStateWhenNoFiles()
        self._clearAndDisabletxtBox()

    def _clearAndDisabletxtBox(self):
        self.txtPrefix.clear()
        self.txtPrefix.setEnabled(False)

        self.txtPostfix.clear()
        self.txtPostfix.setEnabled(False)

        self.txtReplace.clear()
        self.txtReplace.setEnabled(False)

        self.txtBy.clear()
        self.txtBy.setEnabled(False)

        self.txtRegexKeep.clear()
        self.txtRegexKeep.setEnabled(False)

    def _updateStateWhenNoFiles(self):
        self._filesCount = len(self._files)
        self.loadFilesButton.setEnabled(True)
        self.loadFilesButton.setFocus(True)
        self.btnRename.setEnabled(False)

    def _connectSignalsSlots(self):
        self.loadFilesButton.clicked.connect(self.loadFiles)
        self.btnRename.clicked.connect(self.renameFiles)
        self.btnClearCondition.clicked.connect(self._clearAndDisabletxtBox)

        self.txtPrefix.textChanged.connect(self._updateStateWhenReady)
        self.txtPostfix.textChanged.connect(self._updateStateWhenReady)
        self.txtReplace.textChanged.connect(self._updateStateWhenReady)
        self.txtRegexKeep.textChanged.connect(self._updateStateWhenReady)

    def _updateStateWhenReady(self):
        if self.txtPrefix.text() \
                or self.txtPostfix.text() \
                or self.txtReplace.text() \
                or self.txtRegexKeep.text():
            self.btnRename.setEnabled(True)
        else:
            self.btnRename.setEnabled(False)

    def renameFiles(self):
        self._runRenamerThread()
        self._updateStateWhileRenaming()

    def _updateStateWhileRenaming(self):
        self.loadFilesButton.setEnabled(False)
        self.btnRename.setEnabled(False)

    def _runRenamerThread(self):
        prefix = self.txtPrefix.text()
        postfix = self.txtPostfix.text()
        replace = self.txtReplace.text()
        by = self.txtBy.text()
        regexKeep = self.txtRegexKeep.text()
        self._thread = QThread()
        self._renamer = Renamer(
            files=tuple(self._files),
            prefix=prefix,
            postfix=postfix,
            replace=replace,
            by=by,
            regexKeep=regexKeep
        )
        self._renamer.moveToThread(self._thread)
        # Rename
        self._thread.started.connect(self._renamer.renameFiles)
        # Update state
        self._renamer.renamedFile.connect(self._updateStateWhenFileRenamed)
        self._renamer.progressed.connect(self._updateProgressBar)
        self._renamer.finished.connect(self._updateStateWhenNoFiles)
        # Clean up
        self._renamer.finished.connect(self._thread.quit)
        self._renamer.finished.connect(self._renamer.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        # Run the thread
        self._thread.start()

    def _updateProgressBar(self, fileNumber):
        progressPercent = int(fileNumber / self._filesCount * 100)
        self.pgBar.setValue(progressPercent)

    def _updateStateWhenFileRenamed(self, newFile):
        self._files.popleft()
        self.srcFileList.takeItem(0)
        self.dstFileList.addItem(str(newFile))

    def loadFiles(self):
        self.dstFileList.clear()
        if self.dirEdit.text():
            initDir = self.dirEdit.text()
        else:
            initDir = str(Path.home())
        files, filter = QFileDialog.getOpenFileNames(
            self, "Choose Files to Rename", initDir, filter=FILTERS
        )
        if len(files) > 0:
            fileExtension = filter[filter.index("*"): -1]
            self.txtExtension.setText(fileExtension)
            srcDirName = str(Path(files[0]).parent)
            self.dirEdit.setText(srcDirName)
            for file in files:
                self._files.append(Path(file))
                self.srcFileList.addItem(file)
            self._filesCount = len(self._files)

            self._updateStateWhenFilesLoaded()

    def _updateStateWhenFilesLoaded(self):
        self.txtPrefix.setEnabled(True)
        # self.txtPrefix.setFocus(True)
        self.txtPostfix.setEnabled(True)
        self.txtReplace.setEnabled(True)
        self.txtBy.setEnabled(True)
        self.txtRegexKeep.setEnabled(True)
