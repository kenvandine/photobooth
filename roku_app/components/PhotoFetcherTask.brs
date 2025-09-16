' *******************************************************************
' ** PhotoFetcherTask Component - BrightScript Logic
' ** This task runs on the main thread and is safe for networking.
' *******************************************************************

sub init()
  ' -- The main function will be called by the component framework.
  '    It's important that the init() function returns quickly.
  m.top.functionName = "main"
end sub

' This is the main entry point for the Task's thread.
sub main()
  port = createObject("roMessagePort")
  m.top.observeField("control", port)

  while true
    msg = wait(0, port)
    if type(msg) = "roSGNodeEvent"
      if msg.isField("control")
        control = msg.getData()
        if control = "run"
          getPhotos()
        end if
      end if
    end if
  end while
end sub

sub getPhotos()
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
