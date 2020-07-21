import jwt
import bcrypt

from datetime import datetime, timedelta

class UserService:

    def __init__(self, user_dao, config):
        self.user_dao = user_dao
        self.config = config

    def create_new_user(self, new_user):
        new_user['password'] = bcrypt.hashpw(
            new_user['password'].encode('utf-8'),
            bcrypt.gensalt()
        )
        new_user_id = self.user_dao.insert_user(new_user)

        return new_user_id

