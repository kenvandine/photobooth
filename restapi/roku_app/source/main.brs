' *******************************************************************
' ** Main Entry Point
' *******************************************************************

sub Main()
  ' -- Disable the screensaver while the app is running
  appManager = CreateObject("roAppManager")
  if appManager <> invalid
    appManager.SetSystemSupport("screensaver", false)
  end if

  ' -- Create the main scene
  screen = CreateObject("roSGScreen")
  port = CreateObject("roMessagePort")
  screen.setMessagePort(port)

  scene = screen.CreateScene("MainScene")
  screen.show()

  ' -- Event loop
  while true
    msg = wait(1000, port) ' Use a timeout to prevent blocking
    msgType = type(msg)

    if msgType = "roSGScreenEvent"
      if msg.isScreenClosed() then exit while
    end if
  end while
end sub
