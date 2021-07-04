import re
import time
from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSignal


class Renamer(QObject):
    # Define custom signals
    progressed = pyqtSignal(int)
    renamedFile = pyqtSignal(Path)
    finished = pyqtSignal()

    def __init__(self, files, prefix, postfix, replace, by, regexKeep):
        super().__init__()
        self._files = files
        self._prefix = prefix
        self._postfix = postfix
        self._replace = replace
        self._by = by
        self._regexKeep = regexKeep

    def buildNewFileName(self, file, fileNumber):
        newFileName = file.stem

        if self._regexKeep:
            keepResult = re.compile(self._regexKeep, re.VERBOSE).search(file.stem).group()
            if keepResult:
                newFileName = keepResult

        if self._prefix:
            newFileName = self._prefix + newFileName
        # newFileName += file.stem + str(fileNumber)

        if self._replace:
            newFileName = newFileName.replace(self._replace, self._by)

        if self._postfix:
            newFileName += self._postfix
        newFileName += file.suffix

        return file.parent.joinpath(newFileName)

    def renameFiles(self):
        for fileNumber, file in enumerate(self._files, 1):
            # newFile = file.parent.joinpath(f"{self._prefix}{file.stem}{str(fileNumber)}{file.suffix}")
            newFile = self.buildNewFileName(file, fileNumber)
            file.rename(newFile)
            time.sleep(0.1)  # Comment this line to rename files faster.
            self.progressed.emit(fileNumber)
            self.renamedFile.emit(newFile)
        self.progressed.emit(0)  # Reset the progress
        self.finished.emit()
