' *******************************************************************
' ** PhotoFetcherTask Component - BrightScript Logic
' ** This task runs on the main thread and is safe for networking.
' *******************************************************************

sub init()
  print "PhotoFetcherTask: init() function called." ' <-- ADD THIS
  ' Set the name of the function to be run on the task's thread
  m.top.functionName = "getPhotos"
end sub

' This function will be executed on the task's own thread
' when its 'control' field is set to "run".
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
          if json <> invalid and isAssocArray(json) and json.doesExist("photos")
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
