#!/usr/bin/env python

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import argparse
import collections
import itertools
import json
import operator
import os.path
import plistlib
import re
import subprocess
import sys
import os
import warnings

# Most keys can be taken from the USB spec's "HID Usage Tables".
# Apple seems to represent the keys with their "usage page" shifted
# left 32 bits, then or'ed with the key code.
#
# The fn key, though, is special, because it isn't defined by the USB
# spec as far as I know.  Instead, Apple seems to have two versions of
# the fn key in vendor-specific pages.  The first is in page
# kHIDPage_AppleVendorKeyboard (0xff01), the other in page
# kHIDPage_AppleVendorTopCase (0x00ff).  In both pages, the fn key is
# code 3.
#
# References:
# https://developer.apple.com/library/archive/technotes/tn2450/_index.html
# https://opensource.apple.com/source/IOHIDFamily/IOHIDFamily-1035.41.2/IOHIDFamily/AppleHIDUsageTables.h.auto.html
# src/share/apple_hid_usage_tables.hpp in the Karabiner Elements source
# /System/Library/Frameworks/IOKit.framework/Versions/A/Headers/hid/IOHIDUsageTables.h

MASK_USB_KEYBOARD = 7 << 32
MASK_APPLE_KEYBOARD = 0xFF01 << 32
MASK_APPLE_TOP_CASE = 0x00FF << 32

KEY_CODE_TO_NAME = {
    MASK_USB_KEYBOARD | 0x29: "escape",
    MASK_USB_KEYBOARD | 0x39: "caps_lock",
    MASK_USB_KEYBOARD | 0xE0: "left_control",
    MASK_USB_KEYBOARD | 0xE4: "right_control",
    MASK_USB_KEYBOARD | 0xE1: "left_shift",
    MASK_USB_KEYBOARD | 0xE5: "right_shift",
    MASK_USB_KEYBOARD | 0xE2: "left_option",
    MASK_USB_KEYBOARD | 0xE6: "right_option",
    MASK_USB_KEYBOARD | 0xE3: "left_command",
    MASK_USB_KEYBOARD | 0xE7: "right_command",
    MASK_APPLE_KEYBOARD | 0x03: "kb_fn",
    MASK_APPLE_TOP_CASE | 0x03: "top_case_fn",
}

KEY_NAME_TO_CODE = {name: code for code, name in KEY_CODE_TO_NAME.iteritems()}


def get_keyboard_ids():
    hidutil_out = subprocess.check_output(["hidutil", "list", "-m", "keyboard"])
    lines = iter(hidutil_out.splitlines())
    for line in lines:
        if line.lower().strip() == "devices:":
            break
    else:
        raise Exception('Didn\'t find "Devices:" in hidutil output')
    for line in lines:
        fields = line.split()
        if all(
            field in fields
            for field in ["VendorID", "ProductID", "UsagePage", "Usage"]
        ):
            break
    else:
        raise Exception("Didn't find ")
    num_fields = len(fields)
    type_getter = operator.itemgetter(
        fields.index("UsagePage"), fields.index("Usage")
    )
    id_getter = operator.itemgetter(
        fields.index("VendorID"), fields.index("ProductID")
    )
    keyboards = set()
    for line in lines:
        if not line:
            break
        fields = line.split(None, num_fields)
        if len(fields) < num_fields:
            continue
        # Actually, this should never be false since we specified "-m
        # keyboard", but let's be on our guard, I guess.
        if type_getter(fields) == ("1", "6"):
            keyboard_id = tuple(int(val, 16) for val in id_getter(fields))
            # 05AC:8600 is the Touch Bar, according to Karabiner
            # Elements sources.  We can't remap that here (AFAIK).
            if keyboard_id != (0x5AC, 0x8600):
                keyboards.add(keyboard_id)
    return keyboards


def read_modifier_mappings():
    plist_xml = subprocess.check_output(
        ["defaults", "-currentHost", "export", "-g", "-"]
    )
    plist = plistlib.readPlistFromString(plist_xml)
    keyboards = collections.defaultdict(dict)
    for key, val in plist.iteritems():
        match = re.search(
            r"^com\.apple\.keyboard\.modifiermapping\.(\d+)-(\d+)-0$", key
        )
        if match:
            vendor_id = int(match.group(1))
            product_id = int(match.group(2))
            keyboard = (vendor_id, product_id)
            for mapping in val:
                # Sometimes these values are <real> instead of
                # <integer>.  Go home Apple, you're drunk.
                src = int(mapping["HIDKeyboardModifierMappingSrc"])
                dst = int(mapping["HIDKeyboardModifierMappingDst"])
                keyboards[keyboard][src] = dst
    return keyboards


def print_modifier_mappings():
    out = sys.stdout
    out.write("Keyboard remappings\n")
    all_mappings = read_modifier_mappings()
    for keyboard in sorted(get_keyboard_ids()):
        out.write("\nKeyboard %04X:%04X:\n" % keyboard)
        its_mappings = all_mappings[keyboard]
        if its_mappings:
            mapping_strs = [
                "  %s -> %s" % (KEY_CODE_TO_NAME[src], KEY_CODE_TO_NAME[dst])
                for src, dst in its_mappings.iteritems()
            ]
            mapping_strs.sort()
            out.write("\n".join(mapping_strs))
            out.write("\n")
        else:
            out.write("  No remappings\n")


KEY_NAME_ALIASES = {
    # Left/right order important here, see comment in
    # set_modifier_mappings.
    "control": ("left_control", "right_control"),
    "shift": ("left_shift", "right_shift"),
    "option": ("left_option", "right_option"),
    "command": ("left_command", "right_command"),
    "fn": ("kb_fn", "top_case_fn"),
}
KEY_NAME_ALIASES.update((name, (name,)) for name in KEY_NAME_TO_CODE)


def set_modifier_mappings(
    keyboards, mapping_strings, hidutil_path=None, verbose=None
):
    code_mappings = {}
    for mapping_str in mapping_strings:
        src_str, dst_str = re.split(r"\s*,\s*", mapping_str, 1)
        if src_str in ("escape", "caps_lock", "fn"):
            # Apple seems like using the right variant in these cases,
            # rather than the left?  OK...
            dst_str = KEY_NAME_ALIASES[dst_str][-1]
        code_mappings.update(
            (KEY_NAME_TO_CODE[src_name], KEY_NAME_TO_CODE[dst_name])
            for src_name, dst_name in itertools.product(
                KEY_NAME_ALIASES[src_str], KEY_NAME_ALIASES[dst_str]
            )
        )
    all_current_mappings = read_modifier_mappings()
    for keyboard in keyboards:
        kbd_mappings = all_current_mappings[keyboard]
        keyboard_name = "%04X:%04X" % keyboard
        needs_changes = False
        for src_code, dst_code in code_mappings.iteritems():
            if kbd_mappings.get(src_code) != dst_code:
                print(
                    "Keyboard %s: Changing %s -> %s"
                    % (
                        keyboard_name,
                        KEY_CODE_TO_NAME[src_code],
                        KEY_CODE_TO_NAME[dst_code],
                    )
                )
                kbd_mappings[src_code] = dst_code
                needs_changes = True
            elif verbose:
                print(
                    "Keyboard %s: No change %s -> %s"
                    % (
                        keyboard_name,
                        KEY_CODE_TO_NAME[src_code],
                        KEY_CODE_TO_NAME[dst_code],
                    )
                )
        if needs_changes:
            plist = [
                {
                    "HIDKeyboardModifierMappingSrc": src_code,
                    "HIDKeyboardModifierMappingDst": dst_code,
                }
                for src_code, dst_code in kbd_mappings.iteritems()
            ]
            if hidutil_path:
                hidutil_cmd = [
                    hidutil_path,
                    "property",
                    "-m",
                    '{"VendorID": %d, "ProductID": %d}' % keyboard,
                    "-s",
                    json.dumps({"HIDKeyboardModifierMappingPairs": plist}),
                ]
                if verbose:
                    print("Will execute:", " ".join(hidutil_cmd))
                    subprocess.check_call(hidutil_cmd)
            else:
                warnings.warn(
                    (
                        "Modified hidutil not available, modifier changes will"
                        " not work until you log out and back in"
                        # And, in fact, playing with the Keyboard
                        # prefs pane may end up reverting the
                        # preferences we set below.
                    )
                )
            key = "com.apple.keyboard.modifiermapping.%d-%d-0" % keyboard
            defaults_cmd = [
                "defaults",
                "-currentHost",
                "write",
                "-g",
                key,
                plistlib.writePlistToString(plist),
            ]
            if verbose:
                print("Will execute:", " ".join(defaults_cmd))
            subprocess.check_call(defaults_cmd)
            # import Foundation
            # Foundation.CFPreferencesSynchronize(
            #     Foundation.kCFPreferencesAnyApplication,
            #     Foundation.kCFPreferencesCurrentHost,
            #     Foundation.kCFPreferencesCurrentUser,
            # )


def main(argv):
    parser = argparse.ArgumentParser(prog=argv[0])
    subparsers = parser.add_subparsers(dest="command")
    parser_set = subparsers.add_parser("set")
    parser_set.add_argument("mappings", nargs="+")
    parser_set.add_argument(
        "--verbose", "-v", default=False, action="store_true"
    )
    parser_set.add_argument(
        "--keyboard", "-k", dest="keyboards", action="append"
    )
    parser_set.add_argument(
        "--hidutil",
        metavar="PATH",
        help="""\
            Path to modified hidutil.  Needed if you want modifier
            changes to take effect immediately.""",
    )
    subparsers.add_parser("print")
    args = parser.parse_args(argv[1:])
    if args.command == "set":
        if args.keyboards:
            keyboards = {
                tuple(int(id_str, 16) for id_str in keyboard.split(":", 1))
                for keyboard in args.keyboards
            }
        else:
            keyboards = get_keyboard_ids()
        if not args.hidutil:
            our_hidutil = os.path.join(
                os.path.dirname(argv[0]) or ".", "hidtool_modified"
            )
            if os.access(our_hidutil, os.X_OK):
                args.hidutil = our_hidutil
        set_modifier_mappings(
            keyboards, args.mappings, hidutil=args.hidutil, verbose=args.verbose
        )
    elif args.command == "print":
        print_modifier_mappings()


if __name__ == "__main__":
    main(sys.argv)
