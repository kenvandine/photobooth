import React, { useState, useEffect } from 'react';
import './PhotoSlideshow.css';

const PhotoSlideshow = () => {
  const [photos, setPhotos] = useState([]);
  const [currentPhotoIndex, setCurrentPhotoIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isPlaying, setIsPlaying] = useState(true);
  const [slideInterval, setSlideInterval] = useState(5000); // 5 seconds default

  // Fetch photos from the API
  const fetchPhotos = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/photos');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      
      // The API returns an object with a 'photos' array
      if (data && Array.isArray(data.photos) && data.photos.length > 0) {
        setPhotos(data.photos);
        setError(null);
      } else {
        setPhotos([]);
      }
    } catch (err) {
      console.error('Error fetching photos:', err);
      setError('Failed to load photos. Please check if the server is running.');
    } finally {
      setLoading(false);
    }
  };

  // Load photos on component mount
  useEffect(() => {
    fetchPhotos();
    
    // Refresh photos every 30 seconds to catch new uploads
    const refreshInterval = setInterval(fetchPhotos, 30000);
    
    return () => clearInterval(refreshInterval);
  }, []);

  // Slideshow auto-advance
  useEffect(() => {
    if (!isPlaying || photos.length <= 1) return;

    const interval = setInterval(() => {
      setCurrentPhotoIndex((prevIndex) => 
        prevIndex === photos.length - 1 ? 0 : prevIndex + 1
      );
    }, slideInterval);

    return () => clearInterval(interval);
  }, [photos.length, isPlaying, slideInterval, currentPhotoIndex]);

  // Navigation functions
  const goToNext = () => {
    if (photos.length > 0) {
      setCurrentPhotoIndex((prevIndex) => 
        prevIndex === photos.length - 1 ? 0 : prevIndex + 1
      );
    }
  };

  const goToPrevious = () => {
    if (photos.length > 0) {
      setCurrentPhotoIndex((prevIndex) => 
        prevIndex === 0 ? photos.length - 1 : prevIndex - 1
      );
    }
  };

  const goToSlide = (index) => {
    setCurrentPhotoIndex(index);
  };

  const togglePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyPress = (event) => {
      switch (event.key) {
        case 'ArrowLeft':
          goToPrevious();
          break;
        case 'ArrowRight':
          goToNext();
          break;
        case ' ':
          event.preventDefault();
          togglePlayPause();
          break;
        case 'r':
          fetchPhotos();
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [photos.length]);

  if (loading) {
    return (
      <div className="slideshow-container">
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>Loading photos...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="slideshow-container">
        <div className="error">
          <h2>Error</h2>
          <p>{error}</p>
          <button onClick={fetchPhotos} className="retry-button">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (photos.length === 0) {
    return (
      <div className="slideshow-container">
        <div className="no-photos">
          <h2>No Photos Yet</h2>
          <p>Take some photos with the photobooth to see them here!</p>
          <button onClick={fetchPhotos} className="refresh-button">
            Refresh
          </button>
        </div>
      </div>
    );
  }

  const currentPhoto = photos[currentPhotoIndex];

  return (
    <div className="slideshow-container">
      {/* Main photo display */}
      <div className="photo-display">
        <img
          src={`/api/photos/${currentPhoto.id}/file`}
          alt={`Photo ${currentPhotoIndex + 1}`}
          className="main-photo"
          onError={(e) => {
            console.error('Error loading image:', currentPhoto.id);
            e.target.src = '/placeholder-image.jpg'; // Fallback image
          }}
        />
        
        {/* Navigation arrows */}
        <button 
          className="nav-button nav-previous" 
          onClick={goToPrevious}
          disabled={photos.length <= 1}
        >
          &#8249;
        </button>
        <button 
          className="nav-button nav-next" 
          onClick={goToNext}
          disabled={photos.length <= 1}
        >
          &#8250;
        </button>
      </div>

      {/* Controls bar */}
      <div className="controls">
        <button 
          className={`play-pause-button ${isPlaying ? 'playing' : 'paused'}`}
          onClick={togglePlayPause}
        >
          {isPlaying ? '⏸️' : '▶️'}
        </button>
        
        <div className="slide-counter">
          {currentPhotoIndex + 1} / {photos.length}
        </div>
        
        <div className="speed-controls">
          <label>Speed: </label>
          <select 
            value={slideInterval} 
            onChange={(e) => setSlideInterval(Number(e.target.value))}
          >
            <option value={2000}>Fast (2s)</option>
            <option value={5000}>Normal (5s)</option>
            <option value={10000}>Slow (10s)</option>
          </select>
        </div>
        
        <button onClick={fetchPhotos} className="refresh-button">
          🔄 Refresh
        </button>
      </div>

      {/* Thumbnail strip */}
      <div className="thumbnails">
        {photos.map((photo, index) => (
          <button
            key={photo.id}
            className={`thumbnail ${index === currentPhotoIndex ? 'active' : ''}`}
            onClick={() => goToSlide(index)}
          >
            <img
              src={`/api/photos/${photo.id}/file`}
              alt={`Thumbnail ${index + 1}`}
              onError={(e) => {
                e.target.src = '/placeholder-thumbnail.jpg';
              }}
            />
          </button>
        ))}
      </div>

      {/* Keyboard shortcuts help */}
      <div className="help-text">
        Use arrow keys to navigate • Space to play/pause • R to refresh
      </div>
    </div>
  );
};

export default PhotoSlideshow;
