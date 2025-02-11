from pydantic import BaseModel, Field
from typing import List, Sequence, Optional
import gspread


class SheetManager(BaseModel):
    gc: gspread.client.Client
    spreadsheet: gspread.spreadsheet.Spreadsheet
    worksheet  : gspread.worksheet.Worksheet

    class Config:
        arbitrary_types_allowed=True


class SellerData(BaseModel):
    name: str
    address: str    
    gst_number: str


class BuyerData(BaseModel):
    name: str
    address: str    
    gst_number: str



class InvoiceSheetInfo(BaseModel):
    name                            : str
    hsn                             : str
    quantity                        : int
    uom                             : str
    rate                            : float
    basicAmount                     : float
    discount                        : float
    taxableValue                    : float
    cgstRate                        : float
    sgstRate                        : float
    cessRate                        : float
    cgstAmount                      : float
    sgstAmount                      : float
    cessAmount                      : float
    grossValue                      : float

class ValidateInvoiceInfo(BaseModel):
    transaction_id      : int
    invoice_number      : str
    date                : str
        
    seller              : SellerData
    buyer               : BuyerData
        
    items               : Sequence[InvoiceSheetInfo] = Field(default=None)