# Photobooth React Frontend

A React-based slideshow frontend for the photobooth application that displays photos from the `/photos` API endpoint.

## Features

- **Auto-advancing slideshow** with customizable timing (2s, 5s, 10s intervals)
- **Manual navigation** with arrow keys, on-screen buttons, and thumbnail clicks
- **Play/pause functionality** with spacebar control
- **Responsive design** that works on desktop and mobile devices
- **Live refresh** - automatically fetches new photos every 30 seconds
- **Thumbnail strip** for quick navigation
- **Keyboard shortcuts** for easy control
- **Error handling** with retry functionality
- **Loading states** and empty state handling

## Directory Structure

```
reactfrontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── PhotoSlideshow.js
│   │   └── PhotoSlideshow.css
│   ├── App.js
│   ├── App.css
│   ├── index.js
│   ├── index.css
│   └── reportWebVitals.js
├── package.json
└── README.md
```

## Installation

1. Navigate to the `reactfrontend` directory:
   ```bash
   cd restapi/reactfrontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

The application will open at `http://localhost:3000` and proxy API requests to `http://localhost:5000`.

## API Requirements

The frontend expects the following API endpoints:

- `GET /api/photos` - Returns an array of photo objects with `id` field
- `GET /api/photos/{id}` - Returns the actual image file

Example API response for `/api/photos`:
```json
[
  {"id": "photo_20231201_120000.png"},
  {"id": "photo_20231201_120030.png"}
]
```

## Keyboard Controls

- **Left/Right Arrow Keys**: Navigate between photos
- **Spacebar**: Play/pause slideshow
- **R**: Refresh photos from server

## Configuration

The slideshow settings can be adjusted in the component:

- **Slide intervals**: 2s, 5s, or 10s (user-selectable)
- **Auto-refresh interval**: 30 seconds (hardcoded)
- **API proxy**: Configured in package.json to proxy to localhost:5000

## Building for Production

To create a production build:

```bash
npm run build
```

This creates a `build` directory with optimized production files.

## Responsive Design

The slideshow is fully responsive and includes:

- Mobile-optimized controls and navigation
- Flexible thumbnail strip that wraps on small screens
- Touch-friendly button sizing
- Responsive image display that maintains aspect ratio

## Error Handling

The application handles various error states:

- Network connection issues
- Missing or corrupted images
- Empty photo collection
- API server downtime

Each error state provides appropriate user feedback and retry options.

# React Frontend Setup Instructions

## Directory Structure

Create the following directory structure in your `restapi` folder:

```
restapi/
└── reactfrontend/
    ├── public/
    │   └── index.html
    ├── src/
    │   ├
