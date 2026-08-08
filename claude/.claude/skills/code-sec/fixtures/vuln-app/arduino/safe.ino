// Safe Arduino/ESP fixture — the correct variant of every vuln in vuln.ino.
//
// GREEN bed: each rule that FIRES on the matching vuln.ino sink must stay SILENT
// here. Same routes, same entry points, sinks sanitized. Ground truth: ../MANIFEST.md.

#include <WiFi.h>
#include <WebServer.h>
#include <SPIFFS.h>

WebServer server(80);

void handleRead() {
  // SAFE CWE-22 — allowlist maps the request to a fixed path; no user input in the path.
  String name = server.arg("name");
  if (name != "note" && name != "log") { server.send(400); return; }
  File f = SPIFFS.open(name == "note" ? "/data/note.txt" : "/data/log.txt");  // SAFE:CWE-22
  server.send(200, "text/plain", f.readString());
}

void handleGreet() {
  // SAFE CWE-120 — bounded copy, never overflows the buffer.
  char buf[32];
  String who = server.arg("who");
  snprintf(buf, sizeof(buf), "%s", who.c_str());  // SAFE:CWE-120
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
