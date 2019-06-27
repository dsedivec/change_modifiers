This is a bit of code to set modifier remappings on macOS.  I use this to script macOS settings on my machine.

# How It Works

Apple [TN2450][] describes Apple's sanctioned method to set up modifier key mappings in a script.  From my perspective, this has two problems:

1. `UserKeyMapping` changes disappear after reboot.  You need to set up something like a login item to set them every boot.
2. `UserKeyMapping` modifier changes don't appear in System Preferences, and they seem to override changes made in System Preferences.  Imagine months later when I forget that I have a login item that changes my modifier mappings, and I'm going nuts trying to changes them in System Preferences to no avail.

[TN2450]: https://developer.apple.com/library/archive/technotes/tn2450/_index.html

I looked into what `Keyboard.prefPane` does when you change modifiers.  I think it's:

1. Set the appropriate system preferences, which is [kind of well documented](https://apple.stackexchange.com/questions/13598/updating-modifier-key-mappings-through-defaults-command-tool).
2. Twiddle some IOKit properties.

If you do just #1, your modifier remappings don't work until you log out and back in, or just reboot.  Furthermore, System Preferences won't show them, and if you go look, or click something in the modifier mappings there, it may erase the preferences.

I didn't try doing just #2, but I assume those properties will disappear after a reboot.

[`change_mappings.py`][] does both of these things.  Technically, `change_mappings.py` does the properties, then it calls out to a modified version of `hidutil` (which you have to compile; see below) to set the properties.

[`change_mappings.py`]: https://github.com/dsedivec/change_modifiers/blob/master/change_modifiers.py


# Disclaimer

I have barely tested this.  It works for me so far on Mojave.  I think this is using undocumented Apple APIs.  It's liable to screw up your keyboard, or your whole system.  If this explanation didn't make it clear, I only understand about 20% of the Objective-C I modified here.  Use this at your own risk!


# How to Use It

1. Install the Xcode command line tools.
2. Clone this repo.
3. Run `make`.  This should compile `hidutil_modifiers`, which is a modified version of `hidutil` that comes with macOS.
4. Run `change_mappings.py` with appropriate arguments to set modifiers the way you want.

Here's an example:

```
python change_mappings.py caps_lock,control option,command command,option
```

This should remap caps lock to control, and reverse the option and command keys.

You can actually run `change_mappings.py` without `hidutil_modifiers` being available, but you should log out/in after running `change_mappings.py`, or else reboot.


# About the `hidtool` Modifications

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
