
import multiprocessing
import uvicorn

if __name__ == "__main__":
    multiprocessing.freeze_support()
    uvicorn.run("opcda_app:app", host="0.0.0.0", port=8001, reload=False, workers=2)


