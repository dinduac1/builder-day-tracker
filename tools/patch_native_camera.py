"""One-off: ORDO's own camera screen (WebView camera permission), save progress photos to the gallery,
and share a report together with its photo."""
import os
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "android", "app", "src", "main")

m = open(os.path.join(A, "AndroidManifest.xml"), encoding="utf-8").read()
if "android.permission.CAMERA" not in m:
    m = m.replace('    <uses-permission android:name="android.permission.INTERNET" />', '''    <uses-permission android:name="android.permission.INTERNET" />
    <!-- ORDO's own camera screen for progress photos -->
    <uses-permission android:name="android.permission.CAMERA" />
    <uses-feature android:name="android.hardware.camera" android:required="false" />
    <!-- saving progress photos to the gallery on Android 9 and older -->
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" android:maxSdkVersion="28" />''')
open(os.path.join(A, "AndroidManifest.xml"), "w", encoding="utf-8", newline="\n").write(m)

p = os.path.join(A, "java", "com", "builderday", "tracker", "TrackerActivity.java")
s = open(p, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)

rep('''    private Uri cameraUri;                                     // where the camera writes a progress photo''', '''    private Uri cameraUri;                                     // where the camera writes a progress photo
    private static final int RC_CAM = 8;
    private android.webkit.PermissionRequest pendingCam;      // the page asked for the camera; waiting on Android's prompt''')
rep('''            // <input type="file">: profile photos''', '''            // ORDO's camera screen (getUserMedia): ask Android for the camera, then let the page have it
            @Override public void onPermissionRequest(android.webkit.PermissionRequest req) {
                runOnUiThread(() -> {
                    boolean cam = java.util.Arrays.asList(req.getResources()).contains(android.webkit.PermissionRequest.RESOURCE_VIDEO_CAPTURE);
                    if (!cam || !siteHost().equals(req.getOrigin().getHost())) { req.deny(); return; }
                    if (checkSelfPermission(android.Manifest.permission.CAMERA) == android.content.pm.PackageManager.PERMISSION_GRANTED) {
                        req.grant(new String[]{android.webkit.PermissionRequest.RESOURCE_VIDEO_CAPTURE});
                    } else { pendingCam = req; picking = true; requestPermissions(new String[]{android.Manifest.permission.CAMERA}, RC_CAM); }
                });
            }
            // <input type="file">: profile photos, gallery picks''')
rep('''    private Intent cameraIntent() {
        try {''', '''    private Intent cameraIntent() {
        // declaring CAMERA means the phone's camera app also needs the grant
        if (checkSelfPermission(android.Manifest.permission.CAMERA) != android.content.pm.PackageManager.PERMISSION_GRANTED) { cameraUri = null; return null; }
        try {''')
rep('''    @Override
    protected void onActivityResult(int req, int res, Intent data) {''', '''    @Override
    public void onRequestPermissionsResult(int rc, String[] perms, int[] results) {
        super.onRequestPermissionsResult(rc, perms, results);
        if (rc != RC_CAM || pendingCam == null) return;
        if (results.length > 0 && results[0] == android.content.pm.PackageManager.PERMISSION_GRANTED)
            pendingCam.grant(new String[]{android.webkit.PermissionRequest.RESOURCE_VIDEO_CAPTURE});
        else pendingCam.deny();
        pendingCam = null;
    }

    @Override
    protected void onActivityResult(int req, int res, Intent data) {''')
rep('''        @JavascriptInterface public void notify(String title, String body) {''', '''        /** Send text plus a photo (a data: URL) to one app; WhatsApp opens the partner's chat when a number is given. */
        @JavascriptInterface public void shareImageTo(String pkg, String text, String phone, String image) {
            runOnUiThread(() -> {
                Uri u = cacheImage(image, "report.jpg");
                Intent i = new Intent(Intent.ACTION_SEND).putExtra(Intent.EXTRA_TEXT, text);
                if (u != null) i.setType("image/jpeg").putExtra(Intent.EXTRA_STREAM, u).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                else i.setType("text/plain");
                Intent direct = new Intent(i).setPackage(pkg);
                if (phone != null && phone.matches("[0-9]{7,15}") && (pkg.equals("com.whatsapp") || pkg.equals("com.whatsapp.w4b")))
                    direct.putExtra("jid", phone + "@s.whatsapp.net");
                try { startActivity(direct); } catch (Exception e) { startActivity(Intent.createChooser(i, "Send with")); }
            });
        }
        /** Save a progress photo to the phone's gallery (Pictures/ORDO). Returns "" or what went wrong. */
        @JavascriptInterface public String savePhoto(String image, String name) {
            try {
                byte[] bytes = decodeData(image);
                if (bytes == null) return "No photo";
                if (Build.VERSION.SDK_INT >= 29) {
                    android.content.ContentValues v = new android.content.ContentValues();
                    v.put(android.provider.MediaStore.Images.Media.DISPLAY_NAME, name);
                    v.put(android.provider.MediaStore.Images.Media.MIME_TYPE, "image/jpeg");
                    v.put(android.provider.MediaStore.Images.Media.RELATIVE_PATH, "Pictures/ORDO");
                    Uri u = getContentResolver().insert(android.provider.MediaStore.Images.Media.EXTERNAL_CONTENT_URI, v);
                    if (u == null) return "The gallery refused the file";
                    try (java.io.OutputStream o = getContentResolver().openOutputStream(u)) { o.write(bytes); }
                } else {
                    java.io.File dir = new java.io.File(android.os.Environment.getExternalStoragePublicDirectory(android.os.Environment.DIRECTORY_PICTURES), "ORDO");
                    dir.mkdirs();
                    java.io.File f = new java.io.File(dir, name);
                    try (java.io.FileOutputStream o = new java.io.FileOutputStream(f)) { o.write(bytes); }
                    android.media.MediaScannerConnection.scanFile(TrackerActivity.this, new String[]{f.getPath()}, null, null);
                }
                return "";
            } catch (Exception e) { return String.valueOf(e.getMessage()); }
        }
        @JavascriptInterface public void notify(String title, String body) {''')
i = s.rindex("}")
s = s[:i] + '''
    private static byte[] decodeData(String dataUrl) {
        if (dataUrl == null) return null;
        int c = dataUrl.indexOf(',');
        if (!dataUrl.startsWith("data:") || c < 0) return null;
        return android.util.Base64.decode(dataUrl.substring(c + 1), android.util.Base64.DEFAULT);
    }

    /** Write a data: URL image into our cache and share it through FileProvider. */
    private Uri cacheImage(String dataUrl, String name) {
        try {
            byte[] b = decodeData(dataUrl);
            if (b == null) return null;
            java.io.File dir = new java.io.File(getCacheDir(), "photos");
            if (!dir.exists()) dir.mkdirs();
            java.io.File f = new java.io.File(dir, name);
            try (java.io.FileOutputStream o = new java.io.FileOutputStream(f)) { o.write(b); }
            return androidx.core.content.FileProvider.getUriForFile(this, getPackageName() + ".files", f);
        } catch (Exception e) { Log.w(TAG, "share image", e); return null; }
    }
}
'''
if "import android.os.Build;" not in s:
    s = s.replace("import android.os.Bundle;", "import android.os.Build;\nimport android.os.Bundle;")
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
