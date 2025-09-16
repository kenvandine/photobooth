' *******************************************************************
' ** PhotoFetcherTask Component - BrightScript Logic
' ** This task runs on the main thread and is safe for networking.
' *******************************************************************

sub init()
  ' No complex init needed anymore.
  print "PhotoFetcherTask: init() function called." ' <-- ADD THIS
end sub

' This function is called from other components. The OS marshals
' the call to this task's thread, avoiding race conditions.
function run()
  print "PhotoFetcherTask: run() function called." ' <-- ADD THIS
  getPhotos()
end function

sub getPhotos()
  print "PhotoFetcherTask: getPhotos() called." ' <-- ADD THIS
  ' -- Get the API URL from the interface field
  apiUrl = m.top.apiUrl
  if apiUrl = invalid or apiUrl = ""
    print "PhotoFetcherTask: apiUrl is not set."
    return
  end if

  url = apiUrl + "/photos"
  fetcher = createObject("roUrlTransfer")
  fetcher.setUrl(url)
  port = createObject("roMessagePort")
  fetcher.setPort(port)

  if fetcher.asyncGetToString()
    while true
      msg = wait(0, port)
      if type(msg) = "roUrlEvent"
        response = {}
        if msg.getResponseCode() = 200
          json = ParseJSON(msg.getString())
          if json <> invalid and json.isAssocArray() and json.doesExist("photos")
            response.status = "success"
            response.data = json.photos
          else
            response.status = "error"
            response.message = "Invalid JSON response"
          end if
        else
          response.status = "error"
          response.message = "HTTP Error: " + msg.getResponseCode().toStr()
        end if

        ' -- Set the output field to notify the observer
        m.top.response = response
        exit while
      end if
    end while
  else
    m.top.response = { status: "error", message: "asyncGetToString failed" }
  end if
end sub
