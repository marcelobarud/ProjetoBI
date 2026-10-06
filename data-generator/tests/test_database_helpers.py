from projectbi_generator.repositories.master_data import _insert_many_returning


class FakeCursor:
    def __init__(self):
        self.values = []
        self.position = 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def executemany(self, statement, values, returning=False):
        assert returning
        assert "%s" in statement.as_string(None)
        self.values = [913, 427]
        self.position = 0

    def fetchone(self):
        value = self.values[self.position]
        self.position += 1
        return (value,)

    def nextset(self):
        return self.position < len(self.values)


class FakeConnection:
    def cursor(self):
        return FakeCursor()


def test_repository_maps_logical_keys_to_returned_identity_values():
    connection = FakeConnection()
    mapping = _insert_many_returning(
        connection, "core", "stores", ("store_code", "name"),
        [("ST-A", ("ST-A", "A")), ("ST-B", ("ST-B", "B"))], "store_code", "store_id",
    )
    assert mapping == {"ST-A": 913, "ST-B": 427}
