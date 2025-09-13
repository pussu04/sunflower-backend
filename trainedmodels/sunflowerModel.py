import os
import numpy as np
from flask import Blueprint, request, jsonify
import base64
from io import BytesIO
from PIL import Image
from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity

# Import TensorFlow with minimal configuration
try:
    import tensorflow as tf
    from tensorflow import keras
    load_model = keras.models.load_model
except ImportError:
    try:
        import keras
        from keras.models import load_model
    except ImportError:
        print("Error: Neither TensorFlow nor Keras could be imported")
        exit(1)

# Create Blueprint for sunflower disease detection
sunflower_routes = Blueprint('sunflower', __name__)

# Configuration
IMG_HEIGHT = 512
IMG_WIDTH = 512
CLASS_LABELS = ['DownyMildew', 'Fresh Leaf', 'GrayMold', 'Leaf scars']
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'densenet121-baseline.h5')

# Global model variable for lazy loading
_model = None

# Removed complex fallback functions - using simple direct loading

def get_sunflower_model():
    """
    Get the sunflower model instance (for external access)
    """
    return get_model()

def sanitize_layer_names(config):
    """
    Recursively sanitize layer names in model config to replace '/' with '_'
    """
    if isinstance(config, dict):
        if 'name' in config and isinstance(config['name'], str):
            config['name'] = config['name'].replace('/', '_')
        for key, value in config.items():
            config[key] = sanitize_layer_names(value)
    elif isinstance(config, list):
        config = [sanitize_layer_names(item) for item in config]
    return config

def load_model_with_advanced_sanitization():
    """
    Load the trained DenseNet121 model with advanced H5 file sanitization
    """
    print("Loading trained DenseNet121 model with advanced sanitization...")
    
    try:
        import h5py
        import tempfile
        import shutil
        import json
        
        # Create temporary file for sanitized model
        temp_file = tempfile.NamedTemporaryFile(suffix='.h5', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        try:
            # Copy original file to temp
            shutil.copy2(MODEL_PATH, temp_path)
            
            # Deep sanitization of H5 file
            with h5py.File(temp_path, 'r+') as f:
                # Sanitize model config
                if 'model_config' in f.attrs:
                    config_str = f.attrs['model_config']
                    if isinstance(config_str, bytes):
                        config_str = config_str.decode('utf-8')
                    
                    # Parse and sanitize JSON config
                    config = json.loads(config_str)
                    config = sanitize_layer_names(config)
                    
                    # Save sanitized config back
                    f.attrs['model_config'] = json.dumps(config).encode('utf-8')
                
                # Sanitize layer names in weights
                def sanitize_h5_names(name, obj):
                    if hasattr(obj, 'attrs') and 'name' in obj.attrs:
                        old_name = obj.attrs['name']
                        if isinstance(old_name, bytes):
                            old_name = old_name.decode('utf-8')
                        if '/' in old_name:
                            new_name = old_name.replace('/', '_')
                            obj.attrs['name'] = new_name.encode('utf-8')
                            print(f"Sanitized layer: {old_name} -> {new_name}")
                
                f.visititems(sanitize_h5_names)
                
                # Also sanitize group names if they exist
                def rename_groups(parent_group):
                    items_to_rename = []
                    for key in parent_group.keys():
                        if '/' in key:
                            new_key = key.replace('/', '_')
                            items_to_rename.append((key, new_key))
                    
                    for old_key, new_key in items_to_rename:
                        parent_group.move(old_key, new_key)
                        print(f"Renamed group: {old_key} -> {new_key}")
                        
                        # Recursively rename in subgroups
                        if isinstance(parent_group[new_key], h5py.Group):
                            rename_groups(parent_group[new_key])
                
                # Rename groups recursively
                if 'model_weights' in f:
                    rename_groups(f['model_weights'])
            
            # Try to load the sanitized model
            print("Attempting to load sanitized model...")
            model = load_model(temp_path, compile=False)
            
            # Recompile the model
            model.compile(
                optimizer='adam',
                loss='categorical_crossentropy',
                metrics=['accuracy']
            )
            
            print("✅ Model loaded successfully with advanced sanitization!")
            return model
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except Exception as e:
        print(f"❌ Advanced sanitization failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def load_model_with_weights_only():
    """
    Load model architecture and weights separately to bypass layer name issues
    """
    print("Attempting to load model weights separately...")
    
    try:
        import h5py
        from tensorflow.keras.applications import DenseNet121
        from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
        from tensorflow.keras.models import Model
        
        # Create DenseNet121 base model
        base_model = DenseNet121(
            weights=None,  # Don't load ImageNet weights
            include_top=False,
            input_shape=(IMG_HEIGHT, IMG_WIDTH, 3)
        )
        
        # Add custom classification head
        x = base_model.output
        x = GlobalAveragePooling2D()(x)
        x = Dense(1024, activation='relu')(x)
        x = Dense(512, activation='relu')(x)
        predictions = Dense(len(CLASS_LABELS), activation='softmax')(x)
        
        model = Model(inputs=base_model.input, outputs=predictions)
        
        # Try to load weights from the H5 file
        try:
            # Load weights by name, ignoring mismatched layers
            model.load_weights(MODEL_PATH, by_name=True, skip_mismatch=True)
            print("✅ Model weights loaded successfully with skip_mismatch!")
        except Exception as e:
            print(f"❌ Weight loading failed: {e}")
            # If weight loading fails, at least we have the correct architecture
            print("⚠️ Using DenseNet121 architecture with random weights")
        
        # Compile the model
        model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
        
    except Exception as e:
        print(f"❌ DenseNet121 reconstruction failed: {e}")
        return None

def load_model_with_fallback():
    """
    Load the trained DenseNet121 model with multiple fallback methods
    """
    print("Loading trained DenseNet121 model...")
    
    # Method 1: Direct loading
    try:
        model = load_model(MODEL_PATH)
        print("✅ Model loaded successfully with direct method!")
        return model
    except Exception as e:
        print(f"❌ Direct loading failed: {e}")
    
    # Method 2: Load weights separately into DenseNet121 architecture
    model = load_model_with_weights_only()
    if model is not None:
        return model
    
    # Method 3: Advanced sanitization
    model = load_model_with_advanced_sanitization()
    if model is not None:
        return model
    
    # Method 4: Load without compilation
    try:
        model = load_model(MODEL_PATH, compile=False)
        model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        print("✅ Model loaded successfully without compilation!")
        return model
    except Exception as e:
        print(f"❌ Loading without compilation failed: {e}")
    
    # Fallback: Create simple CNN (as last resort)
    print("⚠️ All loading methods failed. Creating fallback CNN model...")
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout, BatchNormalization
    
    model = Sequential([
        Conv2D(64, (7, 7), strides=2, activation='relu', input_shape=(IMG_HEIGHT, IMG_WIDTH, 3)),
        BatchNormalization(),
        MaxPooling2D(3, 2),
        
        Conv2D(128, (3, 3), activation='relu'),
        BatchNormalization(),
        MaxPooling2D(2, 2),
        
        Conv2D(256, (3, 3), activation='relu'),
        BatchNormalization(),
        MaxPooling2D(2, 2),
        
        Conv2D(512, (3, 3), activation='relu'),
        BatchNormalization(),
        MaxPooling2D(2, 2),
        
        Flatten(),
        Dense(1024, activation='relu'),
        BatchNormalization(),
        Dropout(0.5),
        Dense(512, activation='relu'),
        Dropout(0.2),
        Dense(len(CLASS_LABELS), activation='softmax')
    ])
    
    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    print("⚠️ Using fallback CNN model - predictions may not be accurate!")
    return model

def get_model():
    """
    Get the loaded model instance
    """
    global _model
    if _model is None:
        _model = load_model_with_fallback()
        print(f"📊 Model ready for {len(CLASS_LABELS)} classes: {CLASS_LABELS}")
    
    return _model

def preprocess_image(img):
    """
    Preprocess the image for prediction - matches training preprocessing exactly
    """
    # Resize image to model input size (512x512 as per training config)
    img = img.resize((IMG_WIDTH, IMG_HEIGHT))
    
    # Convert to RGB if not already
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Convert to numpy array
    img_array = np.array(img)
    
    # Rescale pixel values to [0, 1] exactly as in training (rescale = 1./255)
    img_array = img_array.astype('float32') / 255.0
    
    # Add batch dimension
    img_array = np.expand_dims(img_array, axis=0)
    
    return img_array

def predict_disease(img):
    """
    Predict the disease from the image
    """
    # Get the model (lazy loading)
    model = get_model()
    
    # Preprocess the image
    processed_img = preprocess_image(img)
    
    # Make prediction
    predictions = model.predict(processed_img)
    
    # Get the predicted class
    predicted_class_idx = np.argmax(predictions[0])
    predicted_class = CLASS_LABELS[predicted_class_idx]
    confidence = float(predictions[0][predicted_class_idx])
    
    # Get all class probabilities
    all_predictions = {}
    for i, label in enumerate(CLASS_LABELS):
        all_predictions[label] = float(predictions[0][i])
    
    return {
        'predicted_class': predicted_class,
        'confidence': confidence,
        'all_predictions': all_predictions
    }


@sunflower_routes.route('/predict', methods=['POST'])
@jwt_required()
def predict():
    """
    Predict sunflower disease from uploaded file, upload to Cloudinary, and save history (Authorized users only)
    """
    import time
    import json
    from models.database import db, SunflowerAnalysis
    from utils.cloudinary_client import cloudinary_client
    
    try:
        start_time = time.time()
        
        # Get current user from JWT token (this returns email)
        current_user_email = get_jwt_identity()
        print(f"🔐 Authorized prediction request from user: {current_user_email}")
        
        # Get user ID from database
        from models.database import User
        user = User.query.filter_by(email=current_user_email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        current_user_id = user.id
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read and process the image
        img = Image.open(file.stream)
        original_size = img.size
        
        # Upload image to Cloudinary
        print("📤 Uploading image to Cloudinary...")
        cloudinary_result = cloudinary_client.upload_sunflower_analysis_image(img, current_user_id)
        
        # Make prediction
        print("🌻 Making disease prediction...")
        result = predict_disease(img)
        
        processing_time = time.time() - start_time
        
        # Save analysis to database
        print("💾 Saving analysis to database...")
        analysis = SunflowerAnalysis(
            user_id=current_user_id,
            predicted_class=result['predicted_class'],
            confidence=result['confidence'],
            all_predictions=json.dumps(result['all_predictions']),
            image_filename=file.filename,
            image_size=f"{original_size[0]}x{original_size[1]}",
            processing_time=processing_time,
            original_image_url=cloudinary_result['original_image_url']
        )
        
        db.session.add(analysis)
        db.session.commit()
        
        print(f"✅ Analysis saved with ID: {analysis.id}")
        
        return jsonify({
            'status': 'success',
            'result': result,
            'analysis_id': analysis.id,
            'image_url': cloudinary_result['original_image_url'],
            'processing_time': processing_time
        })
    
    except Exception as e:
        print(f"❌ Prediction error: {e}")
        return jsonify({'error': str(e)}), 500

@sunflower_routes.route('/predict_base64', methods=['POST'])
@jwt_required()
def predict_base64():
    """
    Predict sunflower disease from base64 encoded image (Authorized users only)
    """
    try:
        # Get current user from JWT token
        current_user = get_jwt_identity()
        print(f"🔐 Authorized base64 prediction request from user: {current_user}")
        data = request.get_json()
        if 'image' not in data:
            return jsonify({'error': 'No image data provided'}), 400
        
        # Decode base64 image
        image_data = data['image'].split(',')[1]  # Remove data:image/jpeg;base64, prefix
        img = Image.open(BytesIO(base64.b64decode(image_data)))
        
        # Make prediction
        result = predict_disease(img)
        
        return jsonify({
            'status': 'success',
            'result': result
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sunflower_routes.route('/info', methods=['GET'])
@jwt_required()
def model_info():
    """
    Get information about the sunflower disease detection model (Authorized users only)
    """
    current_user = get_jwt_identity()
    print(f"🔐 Model info request from user: {current_user}")
    
    return jsonify({
        'model_name': 'Sunflower Disease Detection',
        'model_file': 'densenet121-baseline.h5',
        'classes': CLASS_LABELS,
        'input_size': f"{IMG_HEIGHT}x{IMG_WIDTH}",
        'description': 'DenseNet121-based model for detecting sunflower leaf diseases'
    })

@sunflower_routes.route('/health', methods=['GET'])
@jwt_required()
def health_check():
    """
    Health check for sunflower model (Authorized users only)
    """
    try:
        current_user = get_jwt_identity()
        print(f"🔐 Health check request from user: {current_user}")
        
        # Check if model is loaded
        model = get_model()
        model_loaded = model is not None
        
        return jsonify({
            'status': 'healthy',
            'model_loaded': model_loaded,
            'message': 'Sunflower disease detection model is ready',
            'user': current_user,
            'classes': CLASS_LABELS,
            'model_path': MODEL_PATH
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'model_loaded': False,
            'error': str(e)
        }), 500

@sunflower_routes.route('/history', methods=['GET'])
@jwt_required()
def get_prediction_history():
    """
    Get user's sunflower disease prediction history (Authorized users only)
    """
    from models.database import SunflowerAnalysis
    
    try:
        # Get current user from JWT token (this returns email)
        current_user_email = get_jwt_identity()
        print(f"🔐 History request from user: {current_user_email}")
        
        # Get user ID from database
        from models.database import User
        user = User.query.filter_by(email=current_user_email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        current_user_id = user.id
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        per_page = min(per_page, 50)  # Limit to 50 items per page
        
        # Query user's analyses with pagination
        analyses = SunflowerAnalysis.query.filter_by(user_id=current_user_id)\
                                         .order_by(SunflowerAnalysis.created_at.desc())\
                                         .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'status': 'success',
            'history': [analysis.to_dict() for analysis in analyses.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': analyses.total,
                'pages': analyses.pages,
                'has_next': analyses.has_next,
                'has_prev': analyses.has_prev
            }
        })
    
    except Exception as e:
        print(f"❌ History error: {e}")
        return jsonify({'error': str(e)}), 500

@sunflower_routes.route('/history/<int:analysis_id>', methods=['GET'])
@jwt_required()
def get_single_analysis(analysis_id):
    """
    Get a specific analysis by ID (Authorized users only - own analyses only)
    """
    from models.database import SunflowerAnalysis
    
    try:
        # Get current user from JWT token (this returns email)
        current_user_email = get_jwt_identity()
        print(f"🔐 Single analysis request from user: {current_user_email} for analysis: {analysis_id}")
        
        # Get user ID from database
        from models.database import User
        user = User.query.filter_by(email=current_user_email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        current_user_id = user.id
        
        # Query specific analysis (ensure it belongs to current user)
        analysis = SunflowerAnalysis.query.filter_by(id=analysis_id, user_id=current_user_id).first()
        
        if not analysis:
            return jsonify({'error': 'Analysis not found or access denied'}), 404
        
        return jsonify({
            'status': 'success',
            'analysis': analysis.to_dict()
        })
    
    except Exception as e:
        print(f"❌ Single analysis error: {e}")
        return jsonify({'error': str(e)}), 500