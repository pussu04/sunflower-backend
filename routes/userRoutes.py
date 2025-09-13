from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token
from models.database import db, User
import datetime
from os import getenv, environ
from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError

load_dotenv()

bcrypt = Bcrypt()
user_routes = Blueprint('user_routes', __name__)

# ------------------- REGISTER -------------------
@user_routes.route('/register', methods=['POST'])
def register():
    print("🔄 Registration request started")
    start_time = datetime.datetime.now()
    
    try:
        # Fast JSON parsing
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        username = data.get("username", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        age = data.get("age")

        # Quick validation
        if not all([username, email, password, age]):
            return jsonify({"error": "All fields are required"}), 400

        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400

        # Optimized database check - separate queries for better indexing
        print("🔍 Checking existing users...")
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            return jsonify({"error": "Email already exists"}), 400
            
        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            return jsonify({"error": "Username already exists"}), 400

        print("👤 Creating new user...")
        # Create new user with optimized password hashing
        new_user = User(
            username=username,
            email=email,
            age=int(age)
        )
        new_user.set_password(password)

        # Fast database commit
        db.session.add(new_user)
        db.session.commit()
        
        elapsed = (datetime.datetime.now() - start_time).total_seconds()
        print(f"✅ Registration completed in {elapsed:.2f}s")

        return jsonify({
            "message": "User registered successfully",
            "user": new_user.to_dict()
        }), 201

    except IntegrityError as e:
        db.session.rollback()
        print(f"❌ Integrity error: {e}")
        return jsonify({"error": "Username or email already exists"}), 400
    except ValueError as e:
        db.session.rollback()
        print(f"❌ Validation error: {e}")
        return jsonify({"error": f"Invalid data: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        elapsed = (datetime.datetime.now() - start_time).total_seconds()
        print(f"❌ Registration failed after {elapsed:.2f}s: {e}")
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500

# ------------------- LOGIN -------------------
@user_routes.route('/login', methods=['POST'])
def login():
    print("🔐 Login request started")
    start_time = datetime.datetime.now()
    
    try:
        # Fast JSON parsing
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        print(f"🔍 Looking up user: {email}")
        # Optimized user lookup with only necessary fields
        user = User.query.filter_by(email=email).first()
        if not user:
            print("❌ User not found")
            return jsonify({"error": "Invalid email or password"}), 401

        print("🔑 Checking password...")
        # Fast password verification
        if not user.check_password(password):
            print("❌ Invalid password")
            return jsonify({"error": "Invalid email or password"}), 401

        print("🎫 Creating JWT token...")
        # Create access token using flask-jwt-extended
        access_token = create_access_token(identity=user.email)
        
        elapsed = (datetime.datetime.now() - start_time).total_seconds()
        print(f"✅ Login completed in {elapsed:.2f}s")

        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "user": user.to_dict()
        }), 200

    except Exception as e:
        elapsed = (datetime.datetime.now() - start_time).total_seconds()
        print(f"❌ Login failed after {elapsed:.2f}s: {e}")
        return jsonify({"error": f"Login failed: {str(e)}"}), 500

# ------------------- GET USER PROFILE -------------------
@user_routes.route('/profile/<int:user_id>', methods=['GET'])
def get_profile(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({
            "status": "success",
            "user": user.to_dict()
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get profile: {str(e)}"}), 500

# ------------------- UPDATE USER PROFILE -------------------
@user_routes.route('/profile/<int:user_id>', methods=['PUT'])
def update_profile(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.get_json()
        
        # Update allowed fields
        if 'username' in data:
            # Check if username is already taken by another user
            existing_user = User.query.filter(
                User.username == data['username'],
                User.id != user_id
            ).first()
            if existing_user:
                return jsonify({"error": "Username already exists"}), 400
            user.username = data['username']
        
        if 'age' in data:
            user.age = int(data['age'])
        
        if 'password' in data:
            user.set_password(data['password'])

        db.session.commit()

        return jsonify({
            "message": "Profile updated successfully",
            "user": user.to_dict()
        }), 200

    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Username already exists"}), 400
    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": f"Invalid data: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update profile: {str(e)}"}), 500

# ------------------- DELETE USER -------------------
@user_routes.route('/profile/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        db.session.delete(user)
        db.session.commit()

        return jsonify({"message": "User deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete user: {str(e)}"}), 500

# ------------------- GET ALL USERS (Admin) -------------------
@user_routes.route('/users', methods=['GET'])
def get_all_users():
    try:
        users = User.query.all()
        return jsonify({
            "status": "success",
            "users": [user.to_dict() for user in users],
            "total": len(users)
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get users: {str(e)}"}), 500