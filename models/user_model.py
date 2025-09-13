from flask_bcrypt import Bcrypt
from pymongo.collection import Collection
from bson.objectid import ObjectId

bcrypt = Bcrypt()

class UserModel:
    def __init__(self, users_collection: Collection):
        self.collection = users_collection

    def create_user(self, username: str, email: str, password: str, age: int):
        if self.collection.find_one({"email": email}):
            raise ValueError("Email already exists")

        if self.collection.find_one({"username": username}):
            raise ValueError("Username already exists")

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        user_data = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "age": age
        }

        result = self.collection.insert_one(user_data)
        return str(result.inserted_id)

    def find_by_email(self, email: str):
        return self.collection.find_one({"email": email})

    def verify_password(self, stored_hash: str, password: str) -> bool:
        return bcrypt.check_password_hash(stored_hash, password)

    def get_user_by_id(self, user_id: str):
        return self.collection.find_one({"_id": ObjectId(user_id)})
