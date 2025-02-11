from sheets.sheet_helper import get_workbook, get_sheet
from sheets.invoice_dto import ValidateInvoiceInfo
from tenacity import retry,wait_exponential
from copy import deepcopy
from sheets.invoice_dto import SheetManager


COLUMN_MAPPING = {
    "Transaction ID" : "transaction_id",
    "INVOICE NO" : "invoice_number",
    "Date" : "date",
    "Name": "name",
    "HSN": "hsn",
    "Quantity": "quantity",
    "UOM": "uom",
    "Rate": "rate",
    "Discount": "discount",
    "Basic Amount": "basicAmount",
    "Taxable Value": "taxableValue",
    "CGST Rate" : "cgstRate",
    "CGST Amount": "cgstAmount",
    "SGST Rate": "sgstRate", 
    "SGST Amount": "sgstAmount",
    "CESS Rate": "cessRate",
    "CESS Amount": "cessAmount",
    "Gross Value": "grossValue",
    "Buyer Name": "buyer",
    "Buyer Address":"buyer",
    "Buyer GST": "buyer",
    "Seller Name": "seller",
    "Seller Address":"seller",
    "Seller GST": "seller"

}



class InvoiceSheetHandler:
    def __init__(self, sheet_manager: SheetManager , invoice_info: ValidateInvoiceInfo):        
        self.gc                  = sheet_manager.gc
        self.workbook            = sheet_manager.spreadsheet
        self.sheet               = sheet_manager.worksheet

        self.invoice_info        = invoice_info
    
    def create_invoice(self):
        # data = deepcopy(self.invoice_info)
        data = self.invoice_info.model_dump()
        items = data.get("items", [])
        
        # Ensure items is a list
        if not isinstance(items, list):
            items = [items] if items else []
        
        # # If no items, return a single row with basic invoice info
        # if not items:
        #     headers = self.sheet.row_values(1)
        #     row_data = []
        #     for header in headers:
        #         if header not in COLUMN_MAPPING:
        #             row_data.append("")
        #             continue 

        #         key = COLUMN_MAPPING[header]
        #         if key == "transaction_id":
        #             value = self.invoice_info.transaction_id
        #             row_data.append(value)
        #             continue
                
        #         # Handle different levels of data extraction
        #         if key in ['seller', 'buyer']:
        #             value = data.get(key, {}).get('name', '')
        #         else:
        #             value = data.get(key, "")
                
        #         row_data.append(value)
        #     return [row_data]
        
        # Create rows for each item
        all_rows = []
        for item in items:
            headers = self.sheet.row_values(1)
            row_data = []
            for header in headers:
                if header not in COLUMN_MAPPING:
                    row_data.append("")
                    continue 

                key = COLUMN_MAPPING[header]
                
                # Handle different levels of data extraction
                if key in ['name', 'hsn', 'quantity', 'uom', 'rate', 'basicAmount', 
                           'discount', 'taxableValue', 'cgstAmount', 'sgstAmount', 
                           'cessAmount', 'grossValue', 'cgstRate', 'sgstRate', 'cessRate']:
                    value = item.get(key, "")
                elif key in ['seller', 'buyer']:
                    # value = data.get(key, {}).get('name', '')
                    value = ""
                    if header == "Buyer Name" or header == "Seller Name":
                        value = data.get(key, {}).get('name', '')

                    if not value and (header == "Buyer Address" or header == "Seller Address"):
                        value = data.get(key, {}).get('address', '')
                    if not value and (header == "Buyer GST" or header == "Seller GST"):
                        value = data.get(key, {}).get('gst_number', '')

                else:
                    value = data.get(key, "")
                
                row_data.append(value)
            
            all_rows.append(row_data)
        
        return all_rows
    
    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), reraise=True)
    def add_invoice_row(self, row: list):
        return self.sheet.append_rows(row)
