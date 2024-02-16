import uvicorn

from .api import app


def run_server():
    uvicorn.run(app)


if __name__ == "__main__":
    run_server()
