
class FileObject:
    def __init__(self, content):
        self.content = content

    def save(self, destination):
        with open(destination, 'wb' if isinstance(self.content, bytes) else 'w') as f:
            f.write(self.content)
