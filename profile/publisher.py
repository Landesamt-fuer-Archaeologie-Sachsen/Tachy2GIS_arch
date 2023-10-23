class Publisher:
    def __init__(self):
        self.subscribers = {}
    def get_subscribers(self, event):
        return self.subscribers[event]
    def register(self, event, callback=None):
        if event in self.subscribers:
            self.subscribers[event].append(callback)
        else:
            self.subscribers[event] = [callback]
    def unregister(self, event, callback):
        del self.get_subscribers(event)[callback]
    def publish(self, event, message):
        for callback in self.get_subscribers(event):
            callback(message)

class Publisher:
    def __init__(self):
        self.subscribers = {}
    def get_subscribers(self, event):
        return self.subscribers[event]
    def register(self, event, callback=None):
        if event in self.subscribers:
            self.subscribers[event].append(callback)
        else:
            self.subscribers[event] = [callback]
    def unregister(self, event, callback):
        del self.get_subscribers(event)[callback]
    def publish(self, event, message):
        for callback in self.get_subscribers(event):
            callback(message)
