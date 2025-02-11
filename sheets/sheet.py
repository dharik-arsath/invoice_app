from sheets.sheet_helper import authenticate,get_workbook, get_sheet
from sheets.sheet_dto import ValidateSheetInfo
from tenacity import retry,wait_exponential
from sheets.sheet_dto import SheetManager



data_dict = {
            "transaction_id" : "123",
            "entries":[{"driver_name":"pandi", "date":"2025-01-11","time":"19:14","product_name":"badam milk 456","line":"ss kottai","cases":10,"pieces":10,"discount":0,
                        "commission":187.5,"kuraivu_cases":0,"kuraivu_pieces":1,"kuraivu_amount":4,"adhiga_varavu_cases":0,"adhiga_varavu_pieces":0,"base_amount":4750,
                        "final_amount":4566.5},
                        
                        {"driver_name":"pandi","date":"2025-01-11","time":"19:14","product_name":"200 ml panner (192)","line":"ss kottai","cases":10,"pieces":10,
                        "discount":437.5,"commission":0,"kuraivu_cases":0,"kuraivu_pieces":2,"kuraivu_amount":4,"adhiga_varavu_cases":0,"adhiga_varavu_pieces":0,
                        "base_amount":2000,"final_amount":1566.5}],

            # "expenses":[{"description": "Petrol", "amount": 120},{"description": "Food", "amount": 120}]
            "expenses":[{"Petrol": 120, "Food": 120}]
            }



COLUMN_MAPPING = {
    "ORDER ID" : "",
    "TRANSACTION ID" : "",
    'DATE': 'date',
    'DRIVER NAME': 'driver_name',
    'LINE': 'line',
    'PRODUCT_NAME': "product_name",
    'BASE_AMOUNT': 'base_amount',
    'FINAL_AMOUNT': 'final_amount',
    'DISCOUNT': 'discount',
    'COMMISSION': 'commission',
    "GOODS_UPLOAD_CASES": "goods_upload_cases",
    "GOODS_UPLOAD_PIECES": "goods_upload_pieces",
    "GOODS_RETURN_CASES": "goods_return_cases",
    "GOODS_RETURN_PIECES": "goods_return_pieces",
    "CASE_QUANTITY" : "cases",
    "PIECE_QUANTITY": "pieces",
    'KURAIVU_CASES': 'kuraivu_cases',
    'KURAIVU_PIECES': 'kuraivu_pieces',
    "KURAIVU_AMOUNT" : "kuraivu_amount",
    "ADHIGA_VARAVU_CASES" : "adhiga_varavu_cases" ,
    "ADHIGA_VARAVU_PIECES": "adhiga_varavu_pieces",
    "TIME" : "time",
    "TOTAL EXPENSE" : "",
    "NET AMOUNT" : "",
    "CREDIT PAYABLE": "credit_payable",
    "CREDIT RECEIVABLE": "credit_receivable",
}


class ProductSheetHandler:
    def __init__(self, sheet_manager: SheetManager,  sheet_info: ValidateSheetInfo):
        self.gc             = sheet_manager.gc 
        self.workbook       = sheet_manager.spreadsheet
        self.sheet          = sheet_manager.worksheet
        self.sheet_info     = sheet_info
        self._final_amount   = 0

    
    @property
    def final_amount(self):
        return self._final_amount
    
    @final_amount.setter
    def final_amount(self, val):
        self._final_amount = val 
        return self._final_amount

    def parse_product_entries(self):
        headers = self.sheet.row_values(1)
        row_data = []
        for entry in self.sheet_info.entries:
            row = []
            for header in headers:
                if header not in COLUMN_MAPPING:
                    row.append("")
                    continue 
                
                key = COLUMN_MAPPING[header]
                if hasattr(entry, key):
                    value = getattr(entry, key)
                else:
                    value = ""

                if header == "DISCOUNT":
                    # Sum up all discounts for this entry
                    total_discount = 0
                    for discount in entry.discount:
                        discount_amount = (discount.get('cases', 0) * discount.get('size', 0)) + \
                                        (discount.get('pieces', 0) * (discount.get('size', 0)/24))
                        total_discount += discount_amount
                    value = total_discount

                if header == "COMMISSION":
                    # Sum up all commissions for this entry
                    total_commission = 0
                    for commission in entry.commission:
                        commission_amount = (commission.get('cases', 0) * commission.get('size', 0)) + \
                                          (commission.get('pieces', 0) * (commission.get('size', 0)/24))
                        total_commission += commission_amount
                    value = total_commission

                if header == "ORDER ID":
                    value = self.sheet_info.transaction_id

                if header == "FINAL_AMOUNT":
                    self.final_amount += value 

                row.append(value)

            row_data.append(row)
        

        final_amount = self.final_amount
        credits_payable = self.sheet_info.credits.get("payable", 0)
        credits_receivable = self.sheet_info.credits.get("receivable", 0)

        try:
            net_amout_idx = headers.index("NET AMOUNT")
            row_data[-1][net_amout_idx] = ( final_amount - self.sheet_info.total_expense ) + credits_receivable - credits_payable

            total_expense_idx = headers.index("TOTAL EXPENSE")
            row_data[-1][total_expense_idx] = self.sheet_info.total_expense

            credit_payable_idx = headers.index("CREDIT PAYABLE")
            row_data[-1][credit_payable_idx] = self.sheet_info.credits.get("payable")

            credit_receivable_idx = headers.index("CREDIT RECEIVABLE")
            row_data[-1][credit_receivable_idx] = self.sheet_info.credits.get("receivable")
            
        except Exception as e:  
            print(e)
            print("Not able to find column NET AMOUNT")
        
        return row_data
    
    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), reraise=True)
    def add_product_row(self, rows: list):
        return self.sheet.append_rows(rows)
        

if __name__ == "__main__":
    data_dict = '{"entries":[{"driver_name":"pandi","date":"2025-01-19","time":"19:42","product_name":"badam milk (456)","line":"karia patti","cases":9,"pieces":0,"discount":0,"commission":162,"kuraivu_cases":0,"kuraivu_pieces":0,"kuraivu_amount":0,"adhiga_varavu_cases":0,"adhiga_varavu_pieces":0,"base_amount":4104,"final_amount":3942,"goods_upload_cases":10,"goods_upload_pieces":0,"goods_return_cases":1,"goods_return_pieces":0}],"expenses":{}}'
    import json 
    data_dict = json.loads(data_dict)
    data_dict["transaction_id"] = 123
    data_dict["total_expense"] = 121212
    vsi = ValidateSheetInfo.model_validate(data_dict)

    gc = authenticate()
    # sheet_manager = SheetManager(gc, )
    # sheet = ProductSheetHandler()
