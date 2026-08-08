/* Vulnerable native-C handler — request data copied into a fixed buffer.
 *
 * RED bed for the language:c rule. ast-grep parses .c/.h as language `c`, NOT
 * cpp — the cpp rule pack does NOT run here, so this needs its own c rule
 * (c-bufferoverflow-strcpy). A CGI handler reads attacker input from the
 * environment; there is no bound listener, so the enumerator finds no route
 * here (CGI is fronted by the web server) — this file is a rule bed, not an
 * enumeration bed. Ground truth: ../MANIFEST.md. DO NOT compile and serve. */

#include <string.h>
#include <stdio.h>
#include <stdlib.h>

void handle_request(void) {
  char buf[32];
  const char *who = getenv("QUERY_STRING");  /* attacker-controlled (CGI) */
  strcpy(buf, who);  /* VULN:CWE-120 unbounded copy of request data */
  printf("hello %s\n", buf);
}
