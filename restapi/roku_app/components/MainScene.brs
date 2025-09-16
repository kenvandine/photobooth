' *******************************************************************
' ** MainScene Component - BrightScript Logic
' *******************************************************************

sub init()
  print "MainScene: init() called." ' <-- ADD THIS
  ' -- Find UI components
  m.mainPhoto = m.top.findNode("mainPhoto")
  m.photoCounter = m.top.findNode("photoCounter")
  m.thumbnailStrip = m.top.findNode("thumbnailStrip")
  m.thumbnailStrip.focusable = false
  m.playPauseIndicator = m.top.findNode("playPauseIndicator")

  ' -- Initialize state
  m.photoIndex = 0
  m.photos = []
  m.isPlaying = true
  m.apiUrl = "http://<YOUR_IP_ADDRESS>:5000/api" ' IMPORTANT: Replace <YOUR_IP_ADDRESS> with the actual IP of the server

  ' -- Setup timers
  m.slideshowTimer = m.top.findNode("slideshowTimer")
  if m.slideshowTimer = invalid
    print "MainScene: init() timer." ' <-- ADD THIS
    m.slideshowTimer = createObject("roSGNode", "Timer")
    m.slideshowTimer.duration = 5 ' 5 seconds per slide
    m.slideshowTimer.repeat = true
    m.top.appendChild(m.slideshowTimer) ' Add the timer to the scene
    m.slideshowTimer.ObserveField("fire", "onSlideshowTimerFired")
  end if

  ' -- Add key event observer
  m.top.setFocus(true)

  ' -- Setup the PhotoFetcherTask
  m.photoFetcher = createObject("roSGNode", "PhotoFetcherTask")
  m.photoFetcher.ObserveField("response", "onPhotosReceived")
  m.photoFetcher.apiUrl = m.apiUrl
  print "MainScene: init() END." ' <-- ADD THIS
  m.fadeAnimation = m.top.findNode("fadeAnimation")
  m.fadeInterpolator = m.top.findNode("fadeInterpolator")
  m.fadeAnimation.observeField("state", "onFadeStateChange")
  m.mainPhoto.observeField("loadState", "onPhotoLoadStateChange")
  m.mainPhoto.opacity = 1.0 ' Start fully visible
  m.isFading = false
  m.isFirstPhoto = true
  m.top.ObserveField("focusedChild", "onFirstShow")
end sub

' onFirstShow() is called by the framework after the scene is displayed.
' This is a safer place to make the first call to a task.
sub onFirstShow()
    print "MainScene: onFirstShow() called." ' <-- ADD THIS
    m.photoFetcher.control = "run" ' Initial fetch
end sub

' *******************************************************************
' ** Event Handlers
' *******************************************************************

' onKeyEvent() is a built-in Scene function that handles remote control key presses.
' It returns true if the key was handled, and false otherwise.
function onKeyEvent(key as string, press as boolean) as boolean
  print "MainScene: onKeyEvent() called with key: "; key
  if press and not m.isFading ' Only handle key-down events if not fading
    if key = "right"
      navigate("next")
      return true
    else if key = "left"
      navigate("previous")
      return true
    else if key = "play" or key = "pause" or key = "ok"
      togglePlayPause()
      return true
    end if
  end if
  return false
end function

sub onSlideshowTimerFired()
  if m.isPlaying and m.photos.count() > 1 and not m.isFading
    m.photoIndex = m.photoIndex + 1
    if m.photoIndex >= m.photos.count()
      ' Last photo was shown, refresh the list
      m.photoFetcher.control = "run"
    else
      ' Show next photo
      updateDisplay()
    end if
  end if
end sub

sub onPhotosReceived()
    print "MainScene: onPhotosReceived() called." ' <-- ADD THIS
    response = m.photoFetcher.response
    if response <> invalid and response.status = "success"
        m.photos = response.data
        if m.photos.count() > 0
            m.photoIndex = 0 ' Reset to the first photo
            m.isFirstPhoto = true ' Reset for new photo list
            updateThumbnails()
            updateDisplay()
            if m.photos.count() > 1
                m.slideshowTimer.control = "start"
            end if
        end if
    else
        print "MainScene: Error receiving photos: "; response.message
    end if
end sub

sub onFadeStateChange()
  if m.fadeAnimation.state = "stopped"
    ' If fade out has just finished
    if m.mainPhoto.opacity = 0.0
      ' 2. Update the photo URI, which will trigger the onPhotoLoadStateChange observer
      photoData = m.photos[m.photoIndex]
      photoId = photoData.id
      imageUrl = m.apiUrl + "/photos/" + photoId + "/file"
      m.mainPhoto.uri = imageUrl
      m.photoCounter.text = "Photo " + (m.photoIndex + 1).toStr() + " of " + m.photos.count().toStr()
      m.thumbnailStrip.jumpToItem = m.photoIndex
    else ' Fade in finished
      m.isFading = false
    end if
  end if
end sub

sub onPhotoLoadStateChange()
    if m.mainPhoto.loadState = "loaded"
        ' Only run the fade-in if a fade is in progress.
        ' This prevents a blink on the first photo load.
        if m.isFading
            m.fadeInterpolator.keyValue = [0.0, 1.0]
            m.fadeAnimation.control = "start"
        end if
    else if m.mainPhoto.loadState = "failed"
        ' Handle load failure
        if m.isFading
            print "MainScene: Photo load failed."
            m.isFading = false
        end if
    end if
end sub


' *******************************************************************
' ** Core Logic
' *******************************************************************

sub updateDisplay()
  print "MainScene: updateDisplay() called." ' <-- ADD THIS
  if m.photos.count() = 0 or m.isFading then return

  ' -- Ensure index is within bounds
  if m.photoIndex < 0 or m.photoIndex >= m.photos.count()
    m.photoIndex = 0
  end if

  if m.isFirstPhoto
    m.isFirstPhoto = false
    ' Don't fade, just load the first photo directly
    photoData = m.photos[m.photoIndex]
    photoId = photoData.id
    imageUrl = m.apiUrl + "/photos/" + photoId + "/file"
    m.mainPhoto.uri = imageUrl
    m.photoCounter.text = "Photo " + (m.photoIndex + 1).toStr() + " of " + m.photos.count().toStr()
    m.thumbnailStrip.jumpToItem = m.photoIndex
  else
    ' For all subsequent photos, do the fade transition
    m.isFading = true
    m.fadeInterpolator.keyValue = [1.0, 0.0] ' From opaque to transparent
    m.fadeAnimation.control = "start"
  end if
end sub

sub updateThumbnails()
  content = createObject("roSGNode", "ContentNode")
  for each photo in m.photos
    photoId = photo.id
    thumbnailUrl = m.apiUrl + "/photos/" + photoId + "/file" ' Using full image for thumbnail
    item = content.createChild("ContentNode")
    item.addFields({ thumbnailUrl: thumbnailUrl })
  end for
  m.thumbnailStrip.content = content
end sub

sub navigate(direction as string)
  if m.photos.count() <= 1 then return

  if direction = "next"
    m.photoIndex = (m.photoIndex + 1) mod m.photos.count()
  else if direction = "previous"
    m.photoIndex = m.photoIndex - 1
    if m.photoIndex < 0 then m.photoIndex = m.photos.count() - 1
  end if

  updateDisplay()

  ' -- Reset timer on manual navigation
  if m.isPlaying
    m.slideshowTimer.control = "stop"
    m.slideshowTimer.control = "start"
  end if
end sub

sub togglePlayPause()
  m.isPlaying = not m.isPlaying
  if m.isPlaying
    m.playPauseIndicator.text = "Playing"
    m.slideshowTimer.control = "start"
  else
    m.playPauseIndicator.text = "Paused"
    m.slideshowTimer.control = "stop"
  end if
end sub
