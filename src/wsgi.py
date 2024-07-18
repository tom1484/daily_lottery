from waitress import serve

from app import app, scheduler

if __name__ == "__main__":
    scheduler.init_app(app)
    scheduler.start()
    serve(app, host="0.0.0.0", port=5000)
