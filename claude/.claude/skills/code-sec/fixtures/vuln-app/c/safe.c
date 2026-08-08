/* Safe native-C variant — bounded copy, never overflows the buffer.
 *
 * GREEN bed: the c-bufferoverflow-strcpy rule that fires on vuln.c must stay
 * SILENT here. Same handler, same request source, bounded sink. Ground truth:
 * ../MANIFEST.md. */

#include <string.h>
#include <stdio.h>
#include <stdlib.h>

void handle_request(void) {
  char buf[32];
  const char *who = getenv("QUERY_STRING");
  snprintf(buf, sizeof(buf), "%s", who);  /* SAFE:CWE-120 bounded */
  printf("hello %s\n", buf);
}
