import pytest
import os
import shutil
import json
import base64
from pathlib import Path
from io import BytesIO

# Add the parent directory to the Python path to allow module imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api import app as flask_app

# Define test directories
TEST_UPLOAD_FOLDER = 'test_api_photos'
TEST_METADATA_FOLDER = 'test_photo_metadata'

@pytest.fixture
def client():
    """Pytest fixture to set up a test client and temporary directories."""
    # Configure the Flask app for testing
    flask_app.config['TESTING'] = True
    flask_app.config['UPLOAD_FOLDER'] = TEST_UPLOAD_FOLDER
    flask_app.config['METADATA_FOLDER'] = TEST_METADATA_FOLDER

    # Create a test client
    with flask_app.test_client() as client:
        yield client

    # Teardown: remove temporary directories and their contents
    if os.path.exists(TEST_UPLOAD_FOLDER):
        shutil.rmtree(TEST_UPLOAD_FOLDER)
    if os.path.exists(TEST_METADATA_FOLDER):
        shutil.rmtree(TEST_METADATA_FOLDER)

def create_dummy_image(filename="test.jpg"):
    """Creates a dummy image file for testing."""
    file = BytesIO()
    file.write(b"dummy image data")
    file.name = filename
    file.seek(0)
    return file

def test_upload_photo_with_metadata(client):
    """Test uploading a photo with metadata."""
    image = create_dummy_image()
    data = {
        'file': (image, image.name),
        'title': 'Test Title',
        'description': 'Test Description',
        'tags': 'tag1,tag2,tag3'
    }
    response = client.post('/api/photos', data=data, content_type='multipart/form-data')

    assert response.status_code == 201
    json_data = response.get_json()
    assert 'photo_id' in json_data
    assert json_data['message'] == 'Photo uploaded successfully'

    photo_id = json_data['photo_id']
    metadata_file = os.path.join(TEST_METADATA_FOLDER, f"{photo_id}.json")
    assert os.path.exists(metadata_file)

    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
        assert metadata['title'] == 'Test Title'
        assert metadata['description'] == 'Test Description'
        assert metadata['tags'] == ['tag1', 'tag2', 'tag3']

def test_upload_photo_without_metadata(client):
    """Test uploading a photo without any extra metadata."""
    image = create_dummy_image()
    data = {'file': (image, image.name)}
    response = client.post('/api/photos', data=data, content_type='multipart/form-data')

    assert response.status_code == 201
    json_data = response.get_json()
    assert 'photo_id' in json_data
    photo_id = json_data['photo_id']

    metadata_file = os.path.join(TEST_METADATA_FOLDER, f"{photo_id}.json")
    assert os.path.exists(metadata_file)

def test_upload_photo_base64(client):
    """Test uploading a photo using base64 encoding."""
    image_data = b"dummy base64 image data"
    base64_data = base64.b64encode(image_data).decode('utf-8')
    data = {
        'base64_data': base64_data,
        'file_extension': 'jpg',
        'title': 'Base64 Test'
    }
    response = client.post('/api/photos', data=data)

    assert response.status_code == 201
    json_data = response.get_json()
    assert 'photo_id' in json_data
    photo_id = json_data['photo_id']

    metadata_file = os.path.join(TEST_METADATA_FOLDER, f"{photo_id}.json")
    assert os.path.exists(metadata_file)

    photo_file = os.path.join(TEST_UPLOAD_FOLDER, f"{photo_id}.jpg")
    assert os.path.exists(photo_file)
    with open(photo_file, 'rb') as f:
        assert f.read() == image_data

def test_upload_photo_no_file(client):
    """Test error handling when no file is provided."""
    response = client.post('/api/photos', data={})
    assert response.status_code == 400
    json_data = response.get_json()
    assert 'error' in json_data
    assert json_data['error'] == 'No file or base64 data provided'

def test_upload_photo_invalid_extension(client):
    """Test error handling for invalid file extensions."""
    image = create_dummy_image("test.txt")
    data = {'file': (image, image.name)}
    response = client.post('/api/photos', data=data, content_type='multipart/form-data')

    assert response.status_code == 400
    json_data = response.get_json()
    assert 'error' in json_data
    assert json_data['error'] == 'Invalid file type'

def test_list_photos(client):
    """Test listing all photos."""
    # Upload a few photos first
    client.post('/api/photos', data={'file': (create_dummy_image('test1.jpg'), 'test1.jpg')}, content_type='multipart/form-data')
    client.post('/api/photos', data={'file': (create_dummy_image('test2.jpg'), 'test2.jpg')}, content_type='multipart/form-data')

    response = client.get('/api/photos')
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'photos' in json_data
    assert len(json_data['photos']) == 2
    assert json_data['total'] == 2

def test_get_photo_metadata(client):
    """Test getting metadata for a specific photo."""
    image = create_dummy_image()
    data = {'file': (image, image.name), 'title': 'Specific Photo'}
    response = client.post('/api/photos', data=data, content_type='multipart/form-data')
    photo_id = response.get_json()['photo_id']

    response = client.get(f'/api/photos/{photo_id}')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['id'] == photo_id
    assert json_data['title'] == 'Specific Photo'

def test_get_photo_metadata_not_found(client):
    """Test getting metadata for a non-existent photo."""
    response = client.get('/api/photos/non-existent-id')
    assert response.status_code == 404

def test_download_photo(client):
    """Test downloading a photo file."""
    image = create_dummy_image()
    response = client.post('/api/photos', data={'file': (image, image.name)}, content_type='multipart/form-data')
    photo_id = response.get_json()['photo_id']

    response = client.get(f'/api/photos/{photo_id}/file')
    assert response.status_code == 200
    assert response.data == b"dummy image data"

def test_get_photo_base64(client):
    """Test getting a photo as a base64 string."""
    image_data = b"dummy base64 image data"
    image = BytesIO(image_data)
    image.name = "test.jpg"
    image.seek(0)
    response = client.post('/api/photos', data={'file': (image, image.name)}, content_type='multipart/form-data')
    photo_id = response.get_json()['photo_id']

    response = client.get(f'/api/photos/{photo_id}/base64')
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'base64_data' in json_data
    decoded_data = base64.b64decode(json_data['base64_data'])
    assert decoded_data == image_data

def test_update_photo_metadata(client):
    """Test updating a photo's metadata."""
    response = client.post('/api/photos', data={'file': (create_dummy_image(), 'test.jpg')}, content_type='multipart/form-data')
    photo_id = response.get_json()['photo_id']

    update_data = {'title': 'New Title', 'description': 'New Description'}
    response = client.put(f'/api/photos/{photo_id}', json=update_data)
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['metadata']['title'] == 'New Title'
    assert json_data['metadata']['description'] == 'New Description'

def test_delete_photo(client):
    """Test deleting a photo."""
    response = client.post('/api/photos', data={'file': (create_dummy_image(), 'test.jpg')}, content_type='multipart/form-data')
    photo_id = response.get_json()['photo_id']

    response = client.delete(f'/api/photos/{photo_id}')
    assert response.status_code == 200

    # Verify the photo is deleted
    response = client.get(f'/api/photos/{photo_id}')
    assert response.status_code == 404

def test_search_photos(client):
    """Test searching for photos."""
    client.post('/api/photos', data={'file': (create_dummy_image(), 'a.jpg'), 'title': 'cat photo'}, content_type='multipart/form-data')
    client.post('/api/photos', data={'file': (create_dummy_image(), 'b.jpg'), 'description': 'a dog playing'}, content_type='multipart/form-data')
    client.post('/api/photos', data={'file': (create_dummy_image(), 'c.jpg'), 'tags': 'animal,cat'}, content_type='multipart/form-data')

    response = client.get('/api/photos/search?q=cat')
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['photos']) == 2

    response = client.get('/api/photos/search?q=dog')
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['photos']) == 1
