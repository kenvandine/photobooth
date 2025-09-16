' *******************************************************************
' ** MainScene Component - BrightScript Logic
' *******************************************************************

sub init()
  ' -- Find UI components
  m.mainPhoto = m.top.findNode("mainPhoto")
  m.photoCounter = m.top.findNode("photoCounter")
  m.thumbnailStrip = m.top.findNode("thumbnailStrip")
  m.playPauseIndicator = m.top.findNode("playPauseIndicator")

  ' -- Initialize state
  m.photoIndex = 0
  m.photos = []
  m.isPlaying = true
  m.apiUrl = "http://<YOUR_IP_ADDRESS>:5000/api" ' IMPORTANT: Replace <YOUR_IP_ADDRESS> with the actual IP of the server

  ' -- Setup timers
  m.slideshowTimer = m.top.findNode("slideshowTimer")
  if m.slideshowTimer = invalid
    m.slideshowTimer = createObject("roSGNode", "Timer")
    m.slideshowTimer.duration = 5 ' 5 seconds per slide
    m.slideshowTimer.repeat = true
    m.top.observeField("fire", "onSlideshowTimerFired")
  end if


  ' -- Add key event observer
  m.top.setFocus(true)
  m.top.observeField("wasHotKey", "onKeyEvent")

  ' -- Initial fetch of photos
  getPhotos()
end sub

' *******************************************************************
' ** Event Handlers
' *******************************************************************

function onKeyEvent(event as object) as boolean
  if event.getRoSGNode().isFocused()
    key = event.getKey()
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
      getPhotos()
    else
      ' Show next photo
      updateDisplay()
    end if
  end if
end sub

' *******************************************************************
' ** Core Logic
' *******************************************************************

sub getPhotos()
  url = m.apiUrl + "/photos"
  m.fetcher = createObject("roUrlTransfer")
  m.fetcher.setUrl(url)
  m.fetcher.setPort(createObject("roMessagePort"))
  if m.fetcher.asyncGetToString()
    while true
      msg = wait(0, m.fetcher.getPort())
      if type(msg) = "roUrlEvent"
        if msg.getResponseCode() = 200
          json = ParseJSON(msg.getString())
          if json <> invalid and json.isAssocArray() and json.doesExist("photos")
            m.photos = json.photos
            if m.photos.count() > 0
              m.photoIndex = 0 ' Reset to the first photo
              updateThumbnails()
              updateDisplay()
              m.slideshowTimer.control = "start"
            end if
          end if
        else
          print "Error fetching photos: "; msg.getResponseCode()
        end if
        exit while
      end if
    end while
  end if
end sub

sub updateDisplay()
  if m.photos.count() = 0 then return

  ' -- Ensure index is within bounds
  if m.photoIndex < 0 or m.photoIndex >= m.photos.count()
    m.photoIndex = 0
  end if

  photoData = m.photos[m.photoIndex]
  photoId = photoData.id
  imageUrl = m.apiUrl + "/photos/" + photoId + "/file"

  m.mainPhoto.uri = imageUrl
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
