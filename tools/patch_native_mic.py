"""One-off: let the page use the microphone (voice notes) as well as the camera."""
import os
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "android", "app", "src", "main")
m = open(os.path.join(A, "AndroidManifest.xml"), encoding="utf-8").read()
if "RECORD_AUDIO" not in m:
    m = m.replace('    <uses-permission android:name="android.permission.CAMERA" />', '''    <uses-permission android:name="android.permission.CAMERA" />
    <!-- voice notes in crew chat -->
    <uses-permission android:name="android.permission.RECORD_AUDIO" />
    <uses-permission android:name="android.permission.MODIFY_AUDIO_SETTINGS" />''')
open(os.path.join(A, "AndroidManifest.xml"), "w", encoding="utf-8", newline="\n").write(m)
p = os.path.join(A, "java", "com", "builderday", "tracker", "TrackerActivity.java")
s = open(p, encoding="utf-8").read()
i = s.index("            // ORDO's camera screen (getUserMedia)"); j = s.index("            // <input type=\"file\">", i)
s = s[:i] + '''            // the page asks for the camera (ORDO camera) or microphone (voice notes): ask Android, then let it have them
            @Override public void onPermissionRequest(android.webkit.PermissionRequest req) {
                runOnUiThread(() -> {
                    if (!siteHost().equals(req.getOrigin().getHost())) { req.deny(); return; }
                    java.util.List<String> res = new java.util.ArrayList<>(), need = new java.util.ArrayList<>();
                    for (String r : req.getResources()) {
                        String perm = android.webkit.PermissionRequest.RESOURCE_VIDEO_CAPTURE.equals(r) ? android.Manifest.permission.CAMERA
                                : android.webkit.PermissionRequest.RESOURCE_AUDIO_CAPTURE.equals(r) ? android.Manifest.permission.RECORD_AUDIO : null;
                        if (perm == null) continue;
                        res.add(r);
                        if (checkSelfPermission(perm) != android.content.pm.PackageManager.PERMISSION_GRANTED) need.add(perm);
                    }
                    if (res.isEmpty()) { req.deny(); return; }
                    if (need.isEmpty()) { req.grant(res.toArray(new String[0])); return; }
                    pendingCam = req; pendingRes = res.toArray(new String[0]); picking = true;
                    requestPermissions(need.toArray(new String[0]), RC_CAM);
                });
            }
''' + s[j:]
s = s.replace('''    private android.webkit.PermissionRequest pendingCam;      // the page asked for the camera; waiting on Android's prompt''',
              '''    private android.webkit.PermissionRequest pendingCam;      // the page asked for camera / microphone; waiting on Android's prompt
    private String[] pendingRes;''')
a = '''        if (results.length > 0 && results[0] == android.content.pm.PackageManager.PERMISSION_GRANTED)
            pendingCam.grant(new String[]{android.webkit.PermissionRequest.RESOURCE_VIDEO_CAPTURE});
        else pendingCam.deny();'''
assert a in s
s = s.replace(a, '''        boolean all = results.length > 0;
        for (int r : results) if (r != android.content.pm.PackageManager.PERMISSION_GRANTED) all = false;
        if (all && pendingRes != null) pendingCam.grant(pendingRes); else pendingCam.deny();''')
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
