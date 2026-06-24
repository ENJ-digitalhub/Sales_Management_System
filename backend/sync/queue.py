# backend/sync/queue.py
class Queue:
    def push_to_queue(self, device_id, transaction_id, entity_type, operation, payload):
        """Adds an offline action to the sync queue with the given entity type, operation, and payload."""
        pass
    def process_queue(self):
        """Would read pending items from the DB"""
        pass