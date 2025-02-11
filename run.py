
import uvicorn
import multiprocessing
import views 
import webbrowser

def run_server():

    multiprocessing.freeze_support()


    webbrowser.open("http://localhost:8080")
    uvicorn.run("views:app", host="0.0.0.0", port=8080, reload=False, workers=1)

if __name__ == "__main__":
    run_server()