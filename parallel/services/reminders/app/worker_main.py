from app.worker import ReminderWorker


if __name__ == "__main__":
    worker = ReminderWorker(
        poll_interval=5,
    )

    worker.run()