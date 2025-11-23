'''
Server-Sent Events (SSE) utility module implementing a simple Pub/Sub channel.
'''
import queue

class SSEChannel:
    """A simple pub/sub channel for broadcasting messages to multiple SSE clients.
    Each client gets its own queue when it subscribes via ``listen()``.
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
        """Broadcast a message to all active listeners.
        If a listener's queue raises an exception (e.g., full), it is removed.
        """
        for q in list(self.listeners):
            try:
                q.put_nowait(message)
            except Exception as e:
                print(f"Error publishing to queue: {e}")
                self.unlisten(q)

# Global channel instance used by the app
sse_channel = SSEChannel()
