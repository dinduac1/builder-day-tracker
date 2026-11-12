"""One-off: the app's file picker opens the phone's photo & video grid straight away (Android Photo Picker), with
multi-select; "record a video" opens the video camera."""
import os
J = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "android", "app", "src", "main", "java", "com", "builderday", "tracker", "TrackerActivity.java")
s = open(J, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
rep('''                Intent pick = params.createIntent(), cam = cameraIntent(), launch;
                boolean images = false;
                for (String t : params.getAcceptTypes()) if (t != null && t.startsWith("image")) images = true;
                if (cam != null && images && params.isCaptureEnabled()) launch = cam;          // "Take photo": straight to the camera
                else if (cam != null && images) {                                              // otherwise camera or gallery
                    launch = Intent.createChooser(pick, "Add a photo");
                    launch.putExtra(Intent.EXTRA_INITIAL_INTENTS, new Intent[]{cam});
                } else { launch = pick; cameraUri = null; }''', '''                boolean img = false, vid = false;
                for (String t : params.getAcceptTypes()) {
                    if (t == null) continue;
                    for (String one : t.split(",")) { one = one.trim(); if (one.startsWith("image")) img = true; if (one.startsWith("video")) vid = true; }
                }
                boolean multi = params.getMode() == FileChooserParams.MODE_OPEN_MULTIPLE;
                Intent launch = null;
                cameraUri = null;
                if (params.isCaptureEnabled() && (img || vid))                                  // "Take a photo" / "Record a video"
                    launch = vid && !img ? captureIntent(android.provider.MediaStore.ACTION_VIDEO_CAPTURE, ".mp4") : captureIntent(android.provider.MediaStore.ACTION_IMAGE_CAPTURE, ".jpg");
                if (launch == null && (img || vid)) launch = galleryIntent(img, vid, multi);    // the phone's photo & video grid
                if (launch == null) launch = params.createIntent();''')
rep('''        Uri[] got = WebChromeClient.FileChooserParams.parseResult(res, data);''', '''        Uri[] got = null;
        if (res == RESULT_OK && data != null) {
            if (data.getClipData() != null) {                       // several picked
                android.content.ClipData c = data.getClipData();
                got = new Uri[c.getItemCount()];
                for (int i = 0; i < got.length; i++) got[i] = c.getItemAt(i).getUri();
            } else if (data.getData() != null) got = new Uri[]{data.getData()};
        }''')
rep('''    /** Camera intent that saves full-size into our cache (shared through FileProvider), or null if no camera app. */
    private Intent cameraIntent() {''', '''    /** Android's Photo Picker: every photo and video on the phone in a grid, no storage permission needed. */
    private Intent galleryIntent(boolean img, boolean vid, boolean multi) {
        boolean picker = Build.VERSION.SDK_INT >= 33;
        if (!picker && Build.VERSION.SDK_INT >= 30) {
            try { picker = android.os.ext.SdkExtensions.getExtensionVersion(Build.VERSION_CODES.R) >= 2; } catch (Throwable ignored) { }
        }
        if (picker) {
            Intent i = new Intent(android.provider.MediaStore.ACTION_PICK_IMAGES);
            if (img && !vid) i.setType("image/*"); else if (vid && !img) i.setType("video/*");
            if (multi) {
                int max = 30;
                try { max = Math.min(30, android.provider.MediaStore.getPickImagesMaxLimit()); } catch (Throwable ignored) { }
                i.putExtra(android.provider.MediaStore.EXTRA_PICK_IMAGES_MAX, max);
            }
            return i;
        }
        Intent i = new Intent(Intent.ACTION_GET_CONTENT).addCategory(Intent.CATEGORY_OPENABLE).setType(img && vid ? "*/*" : img ? "image/*" : "video/*");
        if (img && vid) i.putExtra(Intent.EXTRA_MIME_TYPES, new String[]{"image/*", "video/*"});
        if (multi) i.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true);
        return i;
    }

    private Intent captureIntent(String action, String ext) {
        Intent i = cameraIntent();
        if (i == null) return null;
        if (!android.provider.MediaStore.ACTION_IMAGE_CAPTURE.equals(action)) {
            try {
                java.io.File f = new java.io.File(new java.io.File(getCacheDir(), "photos"), "v" + System.currentTimeMillis() + ext);
                cameraUri = androidx.core.content.FileProvider.getUriForFile(this, getPackageName() + ".files", f);
                i = new Intent(action).putExtra(android.provider.MediaStore.EXTRA_OUTPUT, cameraUri)
                        .addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION | Intent.FLAG_GRANT_READ_URI_PERMISSION);
                if (i.resolveActivity(getPackageManager()) == null) { cameraUri = null; return null; }
            } catch (Exception e) { cameraUri = null; return null; }
        }
        return i;
    }

    /** Camera intent that saves full-size into our cache (shared through FileProvider), or null if no camera app. */
    private Intent cameraIntent() {''')
open(J, "w", encoding="utf-8", newline="\n").write(s)
m = os.path.join(os.path.dirname(J), "..", "..", "..", "..", "AndroidManifest.xml")
t = open(m, encoding="utf-8").read()
if "android.media.action.VIDEO_CAPTURE" not in t:
    t = t.replace('''        <intent>
            <action android:name="android.media.action.IMAGE_CAPTURE" />
        </intent>''', '''        <intent>
            <action android:name="android.media.action.IMAGE_CAPTURE" />
        </intent>
        <intent>
            <action android:name="android.media.action.VIDEO_CAPTURE" />
        </intent>''')
open(m, "w", encoding="utf-8", newline="\n").write(t)
print("ok")
