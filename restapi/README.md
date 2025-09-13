# Photo API

A RESTful Flask API for managing photo uploads, storage, and retrieval. This API provides comprehensive photo management functionality including file uploads, metadata storage, search capabilities, and CRUD operations.

## Features

- Upload photos via file upload or base64 encoding
- Store photos on disk with JSON metadata
- Retrieve photos and metadata
- Search functionality by tags, title, or description
- Update and delete operations
- Pagination support
- File size limits and type validation
- UUID-based photo identification

## Installation

1. Install required dependencies:
```bash
pip install flask
```

2. Run the API server:
```bash
python api.py
```

The server will start on `http://localhost:5000`

## File Structure

When running, the API creates the following directories:
- `api_photos/` - Stores uploaded photo files
- `photo_metadata/` - Stores JSON metadata for each photo

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API documentation home page |
| POST | `/api/photos` | Upload a photo |
| GET | `/api/photos` | List all photos with pagination |
| GET | `/api/photos/<id>` | Get metadata for specific photo |
| GET | `/api/photos/<id>/file` | Download photo file |
| GET | `/api/photos/<id>/base64` | Get photo as base64 string |
| PUT | `/api/photos/<id>` | Update photo metadata |
| DELETE | `/api/photos/<id>` | Delete photo and metadata |
| GET | `/api/photos/search?q=<query>` | Search photos |

## Usage Examples

### 1. Upload Photos

#### Upload with metadata:
```bash
curl -X POST \
  -F "file=@$HOME/Pictures/photo.jpg" \
  -F "title=My Birthday Photo" \
  -F "description=A great shot from the party" \
  -F "tags=birthday,party,friends" \
  -F "camera_used=Canon EOS R5" \
  -F "resolution=1920x1080" \
  http://localhost:5000/api/photos
```

#### Simple upload:
```bash
curl -X POST \
  -F "file=@./photo.jpg" \
  http://localhost:5000/api/photos
```

#### Upload via base64:
```bash
# First encode your image
BASE64_DATA=$(base64 -w 0 /path/to/photo.jpg)

curl -X POST \
  -F "base64_data=$BASE64_DATA" \
  -F "file_extension=jpg" \
  -F "title=Base64 Upload" \
  http://localhost:5000/api/photos
```

### 2. Retrieve Photos

#### List all photos:
```bash
curl http://localhost:5000/api/photos
```

#### List with pagination:
```bash
curl "http://localhost:5000/api/photos?page=2&per_page=10"
```

#### Get specific photo metadata:
```bash
curl http://localhost:5000/api/photos/PHOTO_ID_HERE
```

#### Download photo file:
```bash
curl -o downloaded_photo.jpg http://localhost:5000/api/photos/PHOTO_ID_HERE/file
```

#### Get photo as base64:
```bash
curl http://localhost:5000/api/photos/PHOTO_ID_HERE/base64
```

### 3. Search Photos

Search by tags, title, or description:
```bash
curl "http://localhost:5000/api/photos/search?q=birthday"
curl "http://localhost:5000/api/photos/search?q=party"
curl "http://localhost:5000/api/photos/search?q=Canon"
```

### 4. Update Photo Metadata

#### Update multiple fields:
```bash
curl -X PUT \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Title",
    "description": "Updated description",
    "tags": ["updated", "modified", "new-tag"]
  }' \
  http://localhost:5000/api/photos/PHOTO_ID_HERE
```

#### Update single field:
```bash
curl -X PUT \
  -H "Content-Type: application/json" \
  -d '{"title": "New Title"}' \
  http://localhost:5000/api/photos/PHOTO_ID_HERE
```

### 5. Delete Photos

```bash
curl -X DELETE http://localhost:5000/api/photos/PHOTO_ID_HERE
```

## Complete Workflow Example

```bash
# 1. Upload a photo and capture the response
RESPONSE=$(curl -s -X POST \
  -F "file=@$HOME/Pictures/example.jpg" \
  -F "title=Test Photo" \
  -F "description=Testing the API" \
  -F "tags=test,api,demo" \
  http://localhost:5000/api/photos)

# 2. Extract photo ID (requires jq for JSON parsing)
PHOTO_ID=$(echo $RESPONSE | jq -r '.photo_id')
echo "Uploaded photo with ID: $PHOTO_ID"

# 3. Get photo metadata
curl -s http://localhost:5000/api/photos/$PHOTO_ID | jq '.'

# 4. Search for the photo
curl -s "http://localhost:5000/api/photos/search?q=test" | jq '.photos | length'

# 5. Download the photo
curl -o retrieved_photo.jpg http://localhost:5000/api/photos/$PHOTO_ID/file

# 6. Update metadata
curl -s -X PUT \
  -H "Content-Type: application/json" \
  -d '{"description": "Updated via API"}' \
  http://localhost:5000/api/photos/$PHOTO_ID

# 7. Delete the photo
curl -s -X DELETE http://localhost:5000/api/photos/$PHOTO_ID
```

## Response Formats

### Successful Upload Response:
```json
{
  "message": "Photo uploaded successfully",
  "photo_id": "550e8400-e29b-41d4-a716-446655440000",
  "metadata": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "550e8400-e29b-41d4-a716-446655440000.jpg",
    "original_filename": "example.jpg",
    "timestamp": "2024-01-15T10:30:45.123456",
    "file_size": 1024576,
    "file_path": "api_photos/550e8400-e29b-41d4-a716-446655440000.jpg",
    "content_type": "image/jpeg",
    "title": "My Photo",
    "description": "A test photo",
    "tags": ["test", "demo"]
  }
}
```

### List Photos Response:
```json
{
  "photos": [...],
  "total": 25,
  "page": 1,
  "per_page": 20,
  "total_pages": 2
}
```

### Error Response:
```json
{
  "error": "Photo not found"
}
```

## Configuration

### Supported File Types:
- PNG
- JPG/JPEG
- GIF
- BMP
- WEBP

### Limits:
- Maximum file size: 16MB
- Default pagination: 20 photos per page

### Directory Structure:
```
api_photos/               # Uploaded photo files
photo_metadata/           # JSON metadata files
├── photo-id-1.json
├── photo-id-2.json
└── ...
```

## Error Handling

Common HTTP status codes returned:

- `200` - Success
- `201` - Photo uploaded successfully
- `400` - Bad request (invalid file type, missing data, etc.)
- `404` - Photo not found
- `413` - File too large
- `500` - Internal server error

### Common Issues:

1. **File path errors**: Use `$HOME` instead of `~` in curl commands
2. **File permissions**: Ensure files are readable (`chmod 644`)
3. **Unsupported formats**: Only image files are accepted
4. **File size**: Maximum 16MB per file

## Integration with Photobooth

This API can be integrated with the existing photobooth application by modifying the `_take_and_save_photo` method in `main.py` to also POST photos to this API for centralized storage and management.

## License

This API follows the same GPL-3.0 license as the main photobooth application.
