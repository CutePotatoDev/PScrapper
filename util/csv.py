import csv


class CSVWriter:
    def __init__(self, filename, lineterminator="\n", delimiter=";", fieldnames=None, printheader=True):
        self.filename = filename
        self.lineterminator = lineterminator
        self.delimiter = delimiter

        self.fieldnames = fieldnames
        self.printheader = printheader

        # If field names is selected, on class initiation also set field names header line.
        if self.fieldnames is not None and self.printheader:
            with open(self.filename, "w", encoding="UTF-8") as file:
                writer = csv.writer(file, lineterminator=lineterminator, delimiter=delimiter)
                writer.writerow(self.fieldnames)

    # Always overwriting all CSV file. Header and all items from dict.
    def overwriteCSV(self, dict):
        with open(self.filename, "w", encoding="UTF-8") as file:
            writer = csv.writer(file, lineterminator=self.lineterminator, delimiter=self.delimiter)

            if self.fieldnames is not None and self.printheader:
                writer.writerow(self.fieldnames)

            for _, value in dict.items():
                writer.writerow(list(value))
