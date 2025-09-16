' *******************************************************************
' ** Main Entry Point
' *******************************************************************

sub Main()
  ' -- Create the main scene
  screen = CreateObject("roSGScreen")
  port = CreateObject("roMessagePort")
  screen.setMessagePort(port)

  scene = screen.CreateScene("MainScene")
  screen.show()

  ' -- Event loop
  while true
    msg = wait(0, port)
    msgType = type(msg)

    if msgType = "roSGScreenEvent"
      if msg.isScreenClosed() then exit while
    end if
  end while
end sub
