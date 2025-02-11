from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time

import signal
import asyncio
from sheets.invoice_sheet import InvoiceSheetHandler
from sheets.invoice_dto import ValidateInvoiceInfo
from sheets.sheet_helper import (
    SheetManager,
    authenticate,
    generate_numeric_id,
    get_workbook,
    get_sheet,
)
from loguru import logger
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import sys


logger.remove()
# add a file handler
logger.add("logs.log", format="{time} {level} {message}")

IDLE_TIMEOUT = 300  # 300 seconds
shutdown_event = asyncio.Event()  # Used for controlled shutdown


if getattr(sys, 'frozen', False):
    # Running as a PyInstaller bundle
    BASE_DIR = sys._MEIPASS
else:
    # Running as a script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")
STATIC_PATH      = os.path.join(BASE_DIR, "static")
TEMPLATES_PATH   = os.path.join(BASE_DIR, "templates")

print(CREDENTIALS_PATH)
gc = authenticate(CREDENTIALS_PATH)

workbook = get_workbook(gc, "Invoice")
sheet = get_sheet(workbook, "Invoice")
invoice_sheet_manager = SheetManager(gc=gc, spreadsheet=workbook, worksheet=sheet)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Server")
    asyncio.create_task(shutdown_checker())
    yield
    logger.info("Shutting down server")
    shutdown_server()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_PATH), name="static")
template = Jinja2Templates(directory=TEMPLATES_PATH)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["htt"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    # if hasattr(request, "data"):
    #     if request.data is not None:
    #         logger.info("Request: {}".format(request.data))
    body = await request.body()
    if body is not None and len(body.decode("utf-8").strip()) > 0:
        logger.info("Request: {}".format(body.decode("utf-8")))

    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    # logger.info("Response: {}".format(response))
    # logger.info("Response Status: {}".format(response.status_code))
    # logger.info("Response Headers: {}".format(response.headers))

    return response


@app.get("/")
async def render_invoice_template(request: Request):
    return template.TemplateResponse(request=request, name="app.html")


@app.post("/create_invoice")
async def create_invoice(invoice_data: dict[str, object]):
    transaction_id = generate_numeric_id(invoice_sheet_manager)
    invoice_data["transaction_id"] = transaction_id
    print(transaction_id)
    print("**********")

    invoice_sheet_info = ValidateInvoiceInfo(**invoice_data)
    invoice = InvoiceSheetHandler(
        sheet_manager=invoice_sheet_manager, invoice_info=invoice_sheet_info
    )
    invoice_data = invoice.create_invoice()
    all_invoice_rows = invoice.add_invoice_row(invoice_data)
    return all_invoice_rows


# Store last heartbeat timestamp
last_heartbeat = time.time()


@app.get("/heartbeat")
async def heartbeat():
    global last_heartbeat
    last_heartbeat = time.time()
    return {"status": "alive"}


async def shutdown_checker():
    """Background task to monitor idle time and shut down gracefully"""
    global last_heartbeat
    while True:
        await asyncio.sleep(10)  # Check every 10 seconds
        if time.time() - last_heartbeat > IDLE_TIMEOUT:
            print(
                f"No heartbeat received for {IDLE_TIMEOUT} seconds. Shutting down server..."
            )
            shutdown_server()
            break


def shutdown_server():
    """Send a SIGTERM signal to stop Uvicorn properly"""
    signal.raise_signal(signal.SIGTERM)  # Triggers FastAPI's @app.on_event("shutdown")


def run_server():
    import uvicorn
    import multiprocessing

    multiprocessing.freeze_support()

    uvicorn.run("views:app", host="0.0.0.0", port=8080, reload=False, workers=1)


if __name__ == "__main__":
    from run import run_server

    run_server()
