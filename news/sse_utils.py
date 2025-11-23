import queue

class SSEChannel:
    """
    A simple pub/sub channel for broadcasting messages to multiple SSE clients.
    """
    def __init__(self):
        self.listeners = []

    def listen(self):
        """Register a new listener and return its queue."""
        q = queue.Queue()
        self.listeners.append(q)
        return q

    def unlisten(self, q):
        """Unregister a listener."""
        if q in self.listeners:
            self.listeners.remove(q)

    def publish(self, message):
        """Broadcast a message to all active listeners."""
        # Iterate backwards to safely remove if needed (though list.remove handles it)
        # We use a copy of the list to avoid modification during iteration issues
        for q in list(self.listeners):
            try:
                q.put_nowait(message)
            except Exception as e:
                # If a queue is dead or full, we might want to remove it
                print(f"Error publishing to queue: {e}")
                self.unlisten(q)

# Global channel instance
sse_channel = SSEChannel()
