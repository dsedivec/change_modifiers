all: hidutil_modifiers

hidutil_modifiers: *.h *.m
	clang *.m -o $@ -framework Foundation -framework IOKit
