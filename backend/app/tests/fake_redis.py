class FakeRedis:
    def __init__(self):
        self.store = {}

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ex=None):
        self.store[key] = value

    async def delete(self, *keys):
        count = 0
        for k in keys:
            if k in self.store:
                del self.store[k]
                count += 1
        return count

    async def mget(self, *keys):
        return [self.store.get(k) for k in keys]

    async def ping(self):
        return "PONG"

    async def close(self):
        return True

    async def aclose(self):
        return True

    class ConnectionPool:
        async def disconnect(self):
            pass

    @property
    def connection_pool(self):
        return FakeRedis.ConnectionPool()
