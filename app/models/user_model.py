class User:
    dummy_data = {
        1: {'id': 1, 'name': 'Alice'},
        2: {'id': 2, 'name': 'Bob'}
    }

    def __init__(self, id, name):
        self.id = id
        self.name = name

    @classmethod
    def get_by_id(cls, user_id):
        data = cls.dummy_data.get(user_id)
        return cls(**data) if data else None