from datetime import datetime


class Fields:
    DCS = [
        'Name', 'Long name', 'Product price', 'Quantity', 'Model', "Product ID",
        "Creation date", 'URL', 'EAN', 'Manufacturer name', 'Weight', 'TaxClassName',
        'Product image', "Description", 'Categories name', 'INOROUROFSTOCK'
    ]

    SHOPIFY = [
        "Handle", "Title", "Body (HTML)", "Vendor", "Type", "Tags", "Published", "Option1 Name", "Option1 Value", "Option2 Name",
        "Option2 Value", "Option3 Name", "Option3 Value", "Variant SKU", "Variant Grams", "Variant Inventory Tracker",
        "Variant Inventory Qty", "Variant Inventory Policy", "Variant Fulfillment Service", "Variant Price", "Variant Compare At Price",
        "Variant Requires Shipping", "Variant Taxable", "Variant Barcode", "Image Src", "Image Position", "Image Alt Text", "Gift Card",
        "Google Shopping / MPN", "Google Shopping / Age Group", "Google Shopping / Gender", "Google Shopping / Google Product Category",
        "SEO Title", "SEO Description", "Google Shopping / AdWords Grouping", "Google Shopping / AdWords Labels",
        "Google Shopping / Condition", "Google Shopping / Custom Product", "Google Shopping / Custom Label 0",
        "Google Shopping / Custom Label 1", "Google Shopping / Custom Label 2", "Google Shopping / Custom Label 3",
        "Google Shopping / Custom Label 4", "Variant Image", "Variant Weight Unit", "Variant Tax Code", "Cost per item", "Collection"
    ]


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


class DCSItem(Item):
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


class ShopifyItem(Item):
    def __init__(self):
        super().__init__()

        self.vendor = None
        self.type = None
        self.tags = ""
        self.published = True
        self.option1name = None
        self.option1value = None
        self.option2name = None
        self.option2value = None
        self.option3name = None
        self.option3value = None
        self.varinvtracker = None
        self.varprice = None
        self.varcompareatprice = None
        self.varreqshipping = False
        self.vartaxable = True
        self.varbarcode = None
        self.imageposition = None
        self.imagealttext = None
        self.giftcard = False
        self.SEOtitle = None
        self.SEOdescription = None
        self.GSMPN = None
        self.GSagegroup = None
        self.GSgender = None
        self.GSproductcategory = None
        self.GSAdwordsgrouping = None
        self.GSAdwordslabels = None
        self.GScondition = None
        self.GScustomproduct = None
        self.GScustomlabel0 = None
        self.GScustomlabel1 = None
        self.GScustomlabel2 = None
        self.GScustomlabel3 = None
        self.GScustomlabel4 = None
        self.variantimage = None
        self.variantunit = None
        self.varianttaxcode = None
        self.collection = None

    def __iter__(self):
        return iter([
                    self.sku,                   # "Handle"
                    self.itemshortname,         # "Title"
                    self.description,           # "Body (HTML)"
                    self.vendor,                # "Vendor"
                    self.type,                  # "Type"
                    self.tags,                  # "Tags"
                    self.published,             # "Published"
                    self.option1name,           # "Option1 Name"
                    self.option1value,          # "Option1 Value"
                    self.option2name,           # "Option2 Name"
                    self.option2value,          # "Option2 Value"
                    self.option3name,           # "Option3 Name"
                    self.option3value,          # "Option3 Value"
                    self.sku,                   # "Variant SKU"
                    self.weight,                # "Variant Grams"
                    self.varinvtracker,         # "Variant Inventory Tracker"
                    self.stockvalue,            # "Variant Inventory Qty"
                    "deny",                     # "Variant Inventory Policy"
                    "manual",                   # "Variant Fulfillment Service"
                    self.price,                 # "Variant Price"
                    self.varcompareatprice,     # "Variant Compare At Price"
                    self.varreqshipping,        # "Variant Requires Shipping"
                    self.vartaxable,            # "Variant Taxable"
                    self.varbarcode,            # "Variant Barcode"
                    self.image,                 # "Image Src"
                    self.imageposition,         # "Image Position"
                    self.imagealttext,          # "Image Alt Text"
                    self.giftcard,              # "Gift Card"
                    self.GSMPN,                 # "Google Shopping / MPN"
                    self.GSagegroup,            # "Google Shopping / Age Group"
                    self.GSgender,              # "Google Shopping / Gender"
                    self.GSproductcategory,     # "Google Shopping / Google Product Category"
                    self.SEOtitle,              # "SEO Title"
                    self.SEOdescription,        # "SEO Description"
                    self.GSAdwordsgrouping,     # "Google Shopping / AdWords Grouping"
                    self.GSAdwordslabels,       # "Google Shopping / AdWords Labels"
                    self.GScondition,           # "Google Shopping / Condition"
                    self.GScustomproduct,       # "Google Shopping / Custom Product"
                    self.GScustomlabel0,        # "Google Shopping / Custom Label 0"
                    self.GScustomlabel1,        # "Google Shopping / Custom Label 1"
                    self.GScustomlabel2,        # "Google Shopping / Custom Label 2"
                    self.GScustomlabel3,        # "Google Shopping / Custom Label 3"
                    self.GScustomlabel4,        # "Google Shopping / Custom Label 4"
                    self.variantimage,          # "Variant Image"
                    self.variantunit,           # "Variant Weight Unit"
                    self.varianttaxcode,        # "Variant Tax Code"
                    self.price,                 # "Cost per item"
                    self.collection             # "Collection"
                    ])
