from backend.sync.queue import Queue

class ConflictsService:
    @staticmethod
    def get_all_conflicts(session):
        return Queue().get_conflicts(session)

    @staticmethod
    def get_conflict(transaction_id, session):
        return Queue().get_conflict(transaction_id, session)

    @staticmethod
    def resolve_conflict(session, transaction_id, resolution, user_id, note=None):
        return Queue().resolve_conflict(transaction_id, resolution, user_id, note, session)
