def clearDBWatchedStatus():
    from cinemavision import database as DB

    DB.WatchedTrailers.update(watched=False).where(
        DB.WatchedTrailers.watched == 1
    ).execute()
