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

  ' -- Find transition nodes
  m.nextPhoto = m.top.findNode("nextPhoto")
  m.slideAnimation = m.top.findNode("slideAnimation")
  m.slideAnimation.ObserveField("control", "onAnimationFinished")
  m.nextPhoto.ObserveField("loadStatus", "onNextPhotoLoaded")

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
  if press ' Only handle key-down events
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
  if m.isPlaying and m.photos.count() > 0
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
            updateThumbnails()
            updateDisplay()
            m.slideshowTimer.control = "start"
        end if
    else
        print "MainScene: Error receiving photos: "; response.message
    end if
end sub

' *******************************************************************
' ** Core Logic
' *******************************************************************

sub onNextPhotoLoaded()
  if m.nextPhoto.loadStatus = "finished"
    ' The image is ready, now we can start the transition
    m.slideAnimation.control = "start"
  else if m.nextPhoto.loadStatus = "failed"
    ' Handle the error, maybe try to load the next photo?
    ' For now, just log it.
    print "Error: nextPhoto failed to load URI: "; m.nextPhoto.uri
  end if
end sub

sub onAnimationFinished()
  if m.slideAnimation.control = "stop"
    ' Animation has finished, now reset the state for the next transition
    ' The photo that just slid in (nextPhoto) is now our mainPhoto
    m.mainPhoto.uri = m.nextPhoto.uri

    ' Reset the positions of the posters
    m.mainPhoto.translation = [0, 0]
    m.nextPhoto.translation = [1280, 0]
  end if
end sub

sub updateDisplay()
  print "MainScene: updateDisplay() called." ' <-- ADD THIS
  if m.photos.count() = 0 then return

  ' -- Ensure index is within bounds
  if m.photoIndex < 0 or m.photoIndex >= m.photos.count()
    m.photoIndex = 0
  end if

  photoData = m.photos[m.photoIndex]
  photoId = photoData.id
  imageUrl = m.apiUrl + "/photos/" + photoId + "/file"

  ' -- Set the URI for the incoming poster. The animation will be triggered
  ' -- by the onNextPhotoLoaded observer when the image is ready.
  m.nextPhoto.uri = imageUrl

  m.photoCounter.text = "Photo " + (m.photoIndex + 1).toStr() + " of " + m.photos.count().toStr()
  m.thumbnailStrip.jumpToItem = m.photoIndex
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
  if m.photos.count() = 0 then return

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
