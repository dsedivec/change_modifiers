//
//  devices.h
//  IOHIDFamily
//
//  Created by YG on 4/14/16.
//
//

#ifndef devices_h
#define devices_h

#import <Foundation/Foundation.h>

#include <IOKit/hidsystem/IOHIDEventSystemClient.h>
#include <IOKit/hid/IOHIDLib.h>
#include <IOKit/hidsystem/IOHIDServiceClient.h>

// I found this with Google in completely unrelated projects.
// But confirmed it with RE.
#define kOptionErr -6701

#define STATUS_SUCCESS 0
#define STATUS_ERROR   1

#define MATCHING_HELP \
"  -m  --matching..............Set matching services/devices\n" \
"                              Input can be either json style dictionary or common\n" \
"                              device string e.g. keyboard, mouse, digitizer.\n" \
"                                  Supported properties:\n" \
"                                      ProductID        - numeric value (decimal or hex)\n" \
"                                      VendorID         - numeric value (decimal or hex)\n" \
"                                      LocationID       - numeric value (decimal or hex)\n" \
"                                      PrimaryUsagePage - numeric value (decimal or hex)\n" \
"                                      PrimaryUsage     - numeric value (decimal or hex)\n" \
"                                      Transport        - string value\n" \
"                                      Product          - string value\n" \
"                                  For matching against generic properties, you will need to include\n" \
"                                  the \"IOPropertyMatch\" key (see example below).\n" \
"                                  Example strings:\n" \
"                                      'keyboard'\n" \
"                                      'digi'\n" \
"                                      '{\"ProductID\":0x8600,\"VendorID\":0x5ac}'\n" \
"                                      '[{\"ProductID\":0x8600},{\"PrimaryUsagePage\":1,\"PrimaryUsage\":6}]'\n" \
"                                      '{\"IOPropertyMatch\":{\"ReportInterval\":1000}}'\n"

id createPropertiesDicitonary (NSString *str);
NSString * createPropertiesString (const char * str);
NSDictionary *createServiceInfoDictionary(IOHIDServiceClientRef service);
NSDictionary *createDeviceInfoDictionary(IOHIDDeviceRef device);
bool setClientMatching(IOHIDEventSystemClientRef client, const char *str);
bool setManagerMatching(IOHIDManagerRef manager, const char *str);

enum IOHIDEventSystemClientType {
    kIOHIDEventSystemClientTypeMonitor = 1,
    // Keyboard preferences uses 2.  I'm guessing at this name.
    // I don't use this, it's just here FYI.
    kIOHIDEventSystemClientTypeAdmin = 2,
    kIOHIDEventSystemClientTypeSimple = 4
};

extern IOHIDEventSystemClientRef IOHIDEventSystemClientCreateWithType(CFAllocatorRef, enum IOHIDEventSystemClientType, void *);

#endif /* devices_h */
