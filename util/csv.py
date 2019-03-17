import csv


class CSVWriter:
    def __init__(self, filename, lineterminator="\n", delimiter=";", fieldnames=None, printheader=True):
        self.filename = filename
        self.lineterminator = lineterminator
        self.delimiter = delimiter

        self.fieldnames = fieldnames
        self.printheader = printheader

        self._fileid = 0

        # Split files.
        self.splitfile = False
        # Split files into separate ones if size at writing is greater than.
        self.splitmegabytes = 14.95

        # If field names is selected, on class initiation also set field names header line.
        if self.fieldnames is not None and self.printheader:
            with open(self.filename, "w", encoding="UTF-8") as file:
                writer = csv.writer(file, lineterminator=lineterminator, delimiter=delimiter)
                writer.writerow(self.fieldnames)

    def _initWriter(self, filename):
        self._file = open(filename, "w", encoding="UTF-8")
        self._writer = csv.writer(self._file, lineterminator=self.lineterminator, delimiter=self.delimiter)

        if self.fieldnames is not None and self.printheader:
            self._writer.writerow(self.fieldnames)

    # Always overwriting all CSV file. Header and all items from dict.
    def dumpDict(self, dict):
        self._fileid = 0
        self._initWriter(self.filename)

        for _, value in dict.items():
            self._writer.writerow(list(value))

            # Splitting result into couple files. Not best check mechanics because check happens after writing, not before it.
            if (self._file.tell() / 1024) / 1024 > self.splitmegabytes and self.splitfile:
                self._file.close()
                self._fileid += 1
                self._initWriter(self.filename.split(".")[0] + "_" + str(self._fileid) + "." + self.filename.split(".")[1])

        self._file.close()
