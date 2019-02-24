import csv
from datetime import datetime


class Item:
    def __init__(self):
        self.url = None

        self.itemshortname = None
        self.itemlongname = None
        self.price = None
        self.stockvalue = None
        self.sku = None
        self.creationdate = datetime.now().strftime("%Y-%m-%d")
        self.manufacturernumber = None
        self.eancode = None
        self.manufacturer = None
        self.weight = None
        # self.taxclass = "SV"
        self.image = None
        self.description = None
        self.subcategory = None
        # self.instock = 1

    def __iter__(self):
        return iter([self.itemshortname,        # "Name"
                     self.itemlongname,         # "Long name"
                     self.price,                # "Product price"
                     self.stockvalue,           # "Quantity"
                     self.sku,                  # "Model"
                     self.sku,                  # "Product ID"
                     self.creationdate,         # "Creation date"
                     self.manufacturernumber,   # "URL"
                     self.eancode,              # "EAN"
                     self.manufacturer,         # "Manufacturer name"
                     self.weight,               # "Weight"
                     "SV",                      # "TaxClassName"
                     self.image,                # "Product image"
                     self.description,          # "Description"
                     self.subcategory,          # "Categories name"
                     1                          # "INOROUROFSTOCK"
                     ])


class CSVWriter:
    __fieldnames = ['Name', 'Long name', 'Product price', 'Quantity', 'Model', "Product ID",
                    "Creation date", 'URL', 'EAN', 'Manufacturer name', 'Weight', 'TaxClassName',
                    'Product image', "Description", 'Categories name', 'INOROUROFSTOCK']

    def __init__(self, filename, lineterminator="\n", delimiter=";"):
        self.filename = filename
        self.lineterminator = lineterminator
        self.delimiter = delimiter

        with open(self.filename, "w", encoding="UTF-8") as file:
            writer = csv.writer(file, lineterminator=lineterminator, delimiter=delimiter)
            writer.writerow(CSVWriter.__fieldnames)

    def writetoCSV(self, dict):
        with open(self.filename, "w", encoding="UTF-8") as file:
            writer = csv.writer(file, lineterminator=self.lineterminator, delimiter=self.delimiter)
            writer.writerow(CSVWriter.__fieldnames)

            for _, value in dict.items():
                writer.writerow(list(value))
