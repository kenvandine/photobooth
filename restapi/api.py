from flask import Flask, request, jsonify, send_file, current_app
import os
import json
import uuid
from datetime import datetime
import base64
from werkzeug.utils import secure_filename
import mimetypes
from pathlib import Path

app = Flask(__name__)

# Configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# Default configuration
app.config.setdefault('UPLOAD_FOLDER', 'api_photos')
app.config.setdefault('METADATA_FOLDER', 'photo_metadata')
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

@app.before_request
def ensure_directories_exist():
    """Create upload and metadata directories if they don't exist."""
    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(current_app.config['METADATA_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_metadata(photo_id, metadata):
    """Save photo metadata to JSON file."""
    metadata_folder = current_app.config['METADATA_FOLDER']
    metadata_file = os.path.join(metadata_folder, f"{photo_id}.json")
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

def load_metadata(photo_id):
    """Load photo metadata from JSON file."""
    metadata_folder = current_app.config['METADATA_FOLDER']
    metadata_file = os.path.join(metadata_folder, f"{photo_id}.json")
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r') as f:
            return json.load(f)
    return None

def get_all_metadata():
    """Get metadata for all photos."""
    photos = []
    metadata_folder = current_app.config['METADATA_FOLDER']
    if not os.path.exists(metadata_folder):
        return []
    for filename in os.listdir(metadata_folder):
        if filename.endswith('.json'):
            photo_id = filename[:-5]  # Remove .json extension
            metadata = load_metadata(photo_id)
            if metadata:
                photos.append(metadata)
    return photos

@app.route('/api/photos', methods=['POST'])
def upload_photo():
    """Upload a photo with optional metadata."""
    try:
        # Check if the request contains a file
        if 'file' not in request.files and 'base64_data' not in request.form:
            return jsonify({'error': 'No file or base64 data provided'}), 400

        photo_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Handle file upload
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            if not allowed_file(file.filename):
                return jsonify({'error': 'Invalid file type'}), 400

            if file:
                # Generate secure filename
                original_filename = secure_filename(file.filename)
                file_extension = original_filename.rsplit('.', 1)[1].lower()
                filename = f"{photo_id}.{file_extension}"
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                
                # Save the file
                file.save(filepath)
                filepath = os.path.abspath(filepath)
                file_size = os.path.getsize(filepath)
                
        # Handle base64 data
        elif 'base64_data' in request.form:
            base64_data = request.form['base64_data']
            file_extension = request.form.get('file_extension', 'png')
            
            if file_extension not in ALLOWED_EXTENSIONS:
                return jsonify({'error': 'Invalid file extension'}), 400
            
            try:
                # Decode base64 data
                image_data = base64.b64decode(base64_data)
                filename = f"{photo_id}.{file_extension}"
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                
                # Save the file
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                filepath = os.path.abspath(filepath)
                file_size = len(image_data)
                original_filename = f"upload.{file_extension}"
                
            except Exception as e:
                return jsonify({'error': f'Invalid base64 data: {str(e)}'}), 400
        
        # Create metadata
        metadata = {
            'id': photo_id,
            'filename': filename,
            'original_filename': original_filename,
            'timestamp': timestamp,
            'file_size': file_size,
            'file_path': filepath,
            'content_type': mimetypes.guess_type(filepath)[0] or 'application/octet-stream'
        }
        
        # Add optional metadata from form
        optional_fields = ['title', 'description', 'tags', 'camera_used', 'resolution']
        for field in optional_fields:
            if field in request.form:
                if field == 'tags':
                    # Parse tags as comma-separated values
                    metadata[field] = [tag.strip() for tag in request.form[field].split(',') if tag.strip()]
                else:
                    metadata[field] = request.form[field]
        
        # Save metadata
        save_metadata(photo_id, metadata)
        
        return jsonify({
            'message': 'Photo uploaded successfully',
            'photo_id': photo_id,
            'metadata': metadata
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/photos', methods=['GET'])
def list_photos():
    """Get a list of all photos with their metadata."""
    try:
        photos = get_all_metadata()
        
        # Sort by timestamp (newest first)
        photos.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Add pagination support
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        paginated_photos = photos[start_idx:end_idx]
        
        return jsonify({
            'photos': paginated_photos,
            'total': len(photos),
            'page': page,
            'per_page': per_page,
            'total_pages': (len(photos) + per_page - 1) // per_page
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to list photos: {str(e)}'}), 500

@app.route('/api/photos/<photo_id>', methods=['GET'])
def get_photo_metadata(photo_id):
    """Get metadata for a specific photo."""
    try:
        metadata = load_metadata(photo_id)
        if not metadata:
            return jsonify({'error': 'Photo not found'}), 404
            
        return jsonify(metadata)
        
    except Exception as e:
        return jsonify({'error': f'Failed to get photo metadata: {str(e)}'}), 500

@app.route('/api/photos/<photo_id>/file', methods=['GET'])
def download_photo(photo_id):
    """Download the actual photo file."""
    try:
        metadata = load_metadata(photo_id)
        if not metadata:
            return jsonify({'error': 'Photo not found'}), 404
            
        filepath = metadata['file_path']
        if not os.path.exists(filepath):
            return jsonify({'error': 'Photo file not found'}), 404
            
        return send_file(
            filepath,
            as_attachment=False,
            download_name=metadata['original_filename'],
            mimetype=metadata['content_type']
        )
        
    except Exception as e:
        return jsonify({'error': f'Failed to download photo: {str(e)}'}), 500

@app.route('/api/photos/<photo_id>/base64', methods=['GET'])
def get_photo_base64(photo_id):
    """Get photo as base64 encoded string."""
    try:
        metadata = load_metadata(photo_id)
        if not metadata:
            return jsonify({'error': 'Photo not found'}), 404
            
        filepath = metadata['file_path']
        if not os.path.exists(filepath):
            return jsonify({'error': 'Photo file not found'}), 404
            
        with open(filepath, 'rb') as f:
            image_data = f.read()
            base64_data = base64.b64encode(image_data).decode('utf-8')
            
        return jsonify({
            'photo_id': photo_id,
            'base64_data': base64_data,
            'content_type': metadata['content_type'],
            'metadata': metadata
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get photo as base64: {str(e)}'}), 500

@app.route('/api/photos/<photo_id>', methods=['PUT'])
def update_photo_metadata(photo_id):
    """Update metadata for a specific photo."""
    try:
        metadata = load_metadata(photo_id)
        if not metadata:
            return jsonify({'error': 'Photo not found'}), 404
            
        # Update allowed fields
        updatable_fields = ['title', 'description', 'tags']
        updated = False
        
        for field in updatable_fields:
            if field in request.json:
                if field == 'tags':
                    # Ensure tags is a list
                    if isinstance(request.json[field], str):
                        metadata[field] = [tag.strip() for tag in request.json[field].split(',') if tag.strip()]
                    elif isinstance(request.json[field], list):
                        metadata[field] = request.json[field]
                else:
                    metadata[field] = request.json[field]
                updated = True
        
        if updated:
            metadata['updated_at'] = datetime.now().isoformat()
            save_metadata(photo_id, metadata)
            return jsonify({'message': 'Photo metadata updated successfully', 'metadata': metadata})
        else:
            return jsonify({'message': 'No valid fields to update'}), 400
            
    except Exception as e:
        return jsonify({'error': f'Failed to update photo metadata: {str(e)}'}), 500

@app.route('/api/photos/<photo_id>', methods=['DELETE'])
def delete_photo(photo_id):
    """Delete a photo and its metadata."""
    try:
        metadata = load_metadata(photo_id)
        if not metadata:
            return jsonify({'error': 'Photo not found'}), 404
            
        # Delete the photo file
        filepath = metadata['file_path']
        if os.path.exists(filepath):
            os.remove(filepath)
            
        # Delete the metadata file
        metadata_folder = current_app.config['METADATA_FOLDER']
        metadata_file = os.path.join(metadata_folder, f"{photo_id}.json")
        if os.path.exists(metadata_file):
            os.remove(metadata_file)
            
        return jsonify({'message': 'Photo deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': f'Failed to delete photo: {str(e)}'}), 500

@app.route('/api/photos/search', methods=['GET'])
def search_photos():
    """Search photos by tags, title, or description."""
    try:
        query = request.args.get('q', '').lower()
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
            
        photos = get_all_metadata()
        filtered_photos = []
        
        for photo in photos:
            # Search in title
            if 'title' in photo and query in photo['title'].lower():
                filtered_photos.append(photo)
                continue
                
            # Search in description
            if 'description' in photo and query in photo['description'].lower():
                filtered_photos.append(photo)
                continue
                
            # Search in tags
            if 'tags' in photo:
                for tag in photo['tags']:
                    if query in tag.lower():
                        filtered_photos.append(photo)
                        break
        
        # Sort by timestamp (newest first)
        filtered_photos.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return jsonify({
            'photos': filtered_photos,
            'total': len(filtered_photos),
            'query': query
        })
        
    except Exception as e:
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large'}), 413

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
