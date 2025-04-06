from app.models.user_model import User

def find_user_by_id(user_id):
    return User.get_by_id(user_id)