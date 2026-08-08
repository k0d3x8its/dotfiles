// Vulnerable Arduino/ESP fixture — embedded network entry points.
//
// RED bed for the shared rule pack. An ESP WiFi web server is a real network
// entry point (any host that can route to the device reaches it), so the
// enumerator finds each server.on() route AND the ast-grep rules fire on the
// C/C++ sink. Paired safe variants live in ./safe.ino. Ground truth: ../MANIFEST.md.
//
// DO NOT flash this sketch. It is intentionally exploitable.

#include <WiFi.h>
#include <WebServer.h>
#include <SPIFFS.h>

WebServer server(80);

void handleRead() {
  // CWE-22 Path Traversal — request arg concatenated straight into a file path.
  String name = server.arg("name");
  File f = SPIFFS.open("/data/" + name);  // VULN:CWE-22
  server.send(200, "text/plain", f.readString());
}

void handleGreet() {
  // CWE-120 Buffer Overflow — unbounded copy of request data into a fixed buffer.
  char buf[32];
  String who = server.arg("who");
  strcpy(buf, who.c_str());  // VULN:CWE-120
  server.send(200, "text/plain", buf);
}

void setup() {
  WiFi.softAP("device", "");
  server.on("/read", handleRead);
  server.on("/greet", handleGreet);
  server.begin();  // public bind — device joins the WiFi network
}

void loop() {
  server.handleClient();
}
