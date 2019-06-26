This is a modified version of `hidutil` from [Apple's own
sources][src].  Changes are:

* Removed all commands other than `property`
* Made it compile in the absence of what I can only assume are
  internal Apple header files and the like
* **Made it use a "monitor" `IOHIDEventSystemClient` to get and set
  properties**

That last one was the one I really care about, since doing so seems to
allow me to get and set keyboard "properties" that the stock `hidutil`
cannot.  In particular, I wanted to set
`HIDKeyboardModifierMappingPairs`, which seems impossible with stock
`hidutil`.  Ultimately, along with some plist settings, this
*theoretically* allows me to script keyboard modifier remappings in
the same fashion that the "Keyboard" preference pane sets them up.

This is a total hack job and I barely understand what I'm doing.  Use
at your own risk.

[src]: https://opensource.apple.com/source/IOHIDFamily/IOHIDFamily-1090.220.12/
