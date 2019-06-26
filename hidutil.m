//
//  hidutil.c
//  IOHIDFamily
//
//  Created by dekom on 3/10/16.
//
//


#include <stdio.h>
#include <strings.h>
#include <getopt.h>
#include <CoreFoundation/CoreFoundation.h>
#include <IOKit/hidsystem/IOHIDEventSystemClient.h>
#include "hdutil.h"
#include "AssertMacros.h"
#include "utility.h"


extern int property (int argc , const char * argv[]);

const char mainUsage[] =
"\nUsage:\n"
"\n"
"  hidutil [command]\n"
"\n"
"Available commands:\n"
"  property\n"
"\nUse \"hidutil [command] --help\" for more information about a command.\n";



static int printUsage()
{
    printf("%s", mainUsage);
    return STATUS_SUCCESS;
}


int main(int argc, const char * argv[]) {
    
    int   result = STATUS_SUCCESS;
 
    if (argc < 2) {
        return printUsage();
    }
    
    if (strcmp(argv[optind], "help") == 0) {
        return printUsage();
    } else if (strcmp(argv[optind], "property") == 0) {
        result = property (argc, argv);
    } else {
        printf ("ERROR!!! Unknown command %s\n", argv[optind]);
        result = STATUS_ERROR;
    }
  
    if (result == kOptionErr) {
        printUsage();
    }
  
    return result;
}
