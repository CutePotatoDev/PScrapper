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
        self.image = []
        self.description = None
        self.subcategory = None
        # self.instock = 1

    def __iter__(self):
        return iter([self.itemshortname,        # "Name"
                     self.itemlongname,         # "Long name"
                     self.price,                # "Product price"
                     self.stockvalue,           # "Quantity"
                     # self.sku,                  # "Model"
                     self.sku,                  # "Product ID"
                     # self.creationdate,         # "Creation date"
                     self.manufacturernumber,   # "modelnr"
                     self.eancode,              # "EAN"
                     self.manufacturer,         # "Manufacturer name"
                     self.weight,               # "Weight"
                     # "SV",                      # "TaxClassName"
                     ", ".join(self.image),     # "Product image"
                     self.description,          # "Description"
                     self.subcategory           # "Categories name"
                     # 1                          # "INOROUROFSTOCK"
                     ])
