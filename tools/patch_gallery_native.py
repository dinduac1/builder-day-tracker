"""One-off: ORDO's own gallery. The page lists the phone's photos/videos (MediaStore) and loads thumbnails and files from
same-origin /__local/... URLs that the app answers itself (WebView + service-worker request interception)."""
import os
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "android", "app", "src", "main")
J = os.path.join(A, "java", "com", "builderday", "tracker", "TrackerActivity.java")
def edit(path, pairs):
    s = open(path, encoding="utf-8").read()
    for a, b in pairs:
        assert s.count(a) == 1, (os.path.basename(path), s.count(a), a[:70])
        s = s.replace(a, b)
    open(path, "w", encoding="utf-8", newline="\n").write(s)

edit(os.path.join(A, "AndroidManifest.xml"), [('''    <!-- voice notes in crew chat -->''', '''    <!-- ORDO's own gallery in crew chat (photos and videos on the phone) -->
    <uses-permission android:name="android.permission.READ_MEDIA_IMAGES" />
    <uses-permission android:name="android.permission.READ_MEDIA_VIDEO" />
    <uses-permission android:name="android.permission.READ_MEDIA_VISUAL_USER_SELECTED" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="32" />
    <!-- voice notes in crew chat -->''')])

edit(J, [
    ('''    private static final int RC_CAM = 8, RC_LOCK = 9, RC_CONFIRM = 12;''', '''    private static final int RC_CAM = 8, RC_LOCK = 9, RC_CONFIRM = 12, RC_GAL = 13;'''),
    ('''            @Override
            public void onPageFinished(WebView v, String url) {''', '''            @Override
            public android.webkit.WebResourceResponse shouldInterceptRequest(WebView v, WebResourceRequest req) {
                return localMedia(req.getUrl());
            }
            @Override
            public void onPageFinished(WebView v, String url) {'''),
    ('''        if (state != null) web.restoreState(state);''', '''        // requests made through the service worker reach the app here, not through the WebViewClient
        try {
            android.webkit.ServiceWorkerController.getInstance().setServiceWorkerClient(new android.webkit.ServiceWorkerClient() {
                @Override public android.webkit.WebResourceResponse shouldInterceptRequest(WebResourceRequest req) { return localMedia(req.getUrl()); }
            });
        } catch (Throwable t) { Log.w(TAG, "service worker client", t); }
        if (state != null) web.restoreState(state);'''),
    ('''        if (rc != RC_CAM || pendingCam == null) return;''', '''        if (rc == RC_GAL) { js("window.__ordoGalleryPerm && window.__ordoGalleryPerm(" + JSONObject.quote(galleryAccess()) + ")"); return; }
        if (rc != RC_CAM || pendingCam == null) return;'''),
    ('''        @JavascriptInterface public void notify(String title, String body) {''', '''        /** "all", "partial" (Android 14: only some photos allowed) or "none". */
        @JavascriptInterface public String galleryAccess() { return TrackerActivity.this.galleryAccess(); }
        @JavascriptInterface public void askGallery() {
            runOnUiThread(() -> {
                picking = true;
                if (Build.VERSION.SDK_INT >= 34) requestPermissions(new String[]{android.Manifest.permission.READ_MEDIA_IMAGES, android.Manifest.permission.READ_MEDIA_VIDEO, android.Manifest.permission.READ_MEDIA_VISUAL_USER_SELECTED}, RC_GAL);
                else if (Build.VERSION.SDK_INT >= 33) requestPermissions(new String[]{android.Manifest.permission.READ_MEDIA_IMAGES, android.Manifest.permission.READ_MEDIA_VIDEO}, RC_GAL);
                else requestPermissions(new String[]{android.Manifest.permission.READ_EXTERNAL_STORAGE}, RC_GAL);
            });
        }
        @JavascriptInterface public void openAppSettings() {
            runOnUiThread(() -> { picking = true; startActivity(new Intent(android.provider.Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:" + getPackageName()))); });
        }
        /** Newest first. kind: "all" | "image" | "video". Each: {id, type, w, h, dur (s), size, date}. */
        @JavascriptInterface public String galleryPage(int offset, int limit, String kind) {
            org.json.JSONArray out = new org.json.JSONArray();
            try {
                Uri files = android.provider.MediaStore.Files.getContentUri("external");
                java.util.List<String> proj = new java.util.ArrayList<>(java.util.Arrays.asList("_id", "media_type", "mime_type", "width", "height", "date_added", "_size"));
                if (Build.VERSION.SDK_INT >= 29) proj.add("duration");
                Bundle args = new Bundle();
                args.putString(android.content.ContentResolver.QUERY_ARG_SQL_SELECTION, "image".equals(kind) ? "media_type=1" : "video".equals(kind) ? "media_type=3" : "media_type=1 OR media_type=3");
                args.putString(android.content.ContentResolver.QUERY_ARG_SQL_SORT_ORDER, "date_added DESC");
                args.putInt(android.content.ContentResolver.QUERY_ARG_LIMIT, Math.max(1, Math.min(200, limit)));
                args.putInt(android.content.ContentResolver.QUERY_ARG_OFFSET, Math.max(0, offset));
                try (android.database.Cursor c = getContentResolver().query(files, proj.toArray(new String[0]), args, null)) {
                    if (c != null) while (c.moveToNext()) {
                        boolean video = c.getInt(1) == 3;
                        org.json.JSONObject o = new org.json.JSONObject().put("id", c.getLong(0)).put("type", video ? "video" : "image")
                                .put("mime", c.getString(2)).put("w", c.getInt(3)).put("h", c.getInt(4)).put("date", c.getLong(5)).put("size", c.getLong(6));
                        if (proj.size() > 7) o.put("dur", c.getLong(7) / 1000.0);
                        out.put(o);
                    }
                }
            } catch (Exception e) { Log.w(TAG, "gallery", e); }
            return out.toString();
        }
        @JavascriptInterface public void notify(String title, String body) {'''),
    ('''    private void deliverOpen() {''', '''    private String galleryAccess() {
        java.util.function.Predicate<String> ok = p -> checkSelfPermission(p) == android.content.pm.PackageManager.PERMISSION_GRANTED;
        if (Build.VERSION.SDK_INT >= 33) {
            if (ok.test(android.Manifest.permission.READ_MEDIA_IMAGES) || ok.test(android.Manifest.permission.READ_MEDIA_VIDEO)) return "all";
            if (Build.VERSION.SDK_INT >= 34 && ok.test(android.Manifest.permission.READ_MEDIA_VISUAL_USER_SELECTED)) return "partial";
            return "none";
        }
        return ok.test(android.Manifest.permission.READ_EXTERNAL_STORAGE) ? "all" : "none";
    }

    /** /__local/thumb|file/image|video/<id> on our own site: answered from the phone's media store, never the network. */
    private android.webkit.WebResourceResponse localMedia(Uri u) {
        try {
            if (u == null || !siteHost().equals(u.getHost())) return null;
            java.util.List<String> p = u.getPathSegments();
            if (p.size() != 4 || !"__local".equals(p.get(0))) return null;
            boolean video = "video".equals(p.get(2));
            long id = Long.parseLong(p.get(3));
            Uri item = android.content.ContentUris.withAppendedId(video ? android.provider.MediaStore.Video.Media.EXTERNAL_CONTENT_URI : android.provider.MediaStore.Images.Media.EXTERNAL_CONTENT_URI, id);
            java.util.Map<String, String> h = new java.util.HashMap<>();
            h.put("Cache-Control", "private, max-age=3600");
            android.content.ContentResolver cr = getContentResolver();
            if ("thumb".equals(p.get(1))) {
                android.graphics.Bitmap b;
                if (Build.VERSION.SDK_INT >= 29) b = cr.loadThumbnail(item, new android.util.Size(360, 360), null);
                else b = video ? android.provider.MediaStore.Video.Thumbnails.getThumbnail(cr, id, android.provider.MediaStore.Video.Thumbnails.MINI_KIND, null)
                               : android.provider.MediaStore.Images.Thumbnails.getThumbnail(cr, id, android.provider.MediaStore.Images.Thumbnails.MINI_KIND, null);
                if (b == null) return new android.webkit.WebResourceResponse("text/plain", "utf-8", 404, "Not Found", h, new java.io.ByteArrayInputStream(new byte[0]));
                java.io.ByteArrayOutputStream o = new java.io.ByteArrayOutputStream();
                b.compress(android.graphics.Bitmap.CompressFormat.JPEG, 82, o);
                return new android.webkit.WebResourceResponse("image/jpeg", null, 200, "OK", h, new java.io.ByteArrayInputStream(o.toByteArray()));
            }
            if ("file".equals(p.get(1))) {
                String mime = cr.getType(item);
                return new android.webkit.WebResourceResponse(mime != null ? mime : (video ? "video/mp4" : "image/jpeg"), null, 200, "OK", h, cr.openInputStream(item));
            }
        } catch (Exception e) { Log.w(TAG, "local media", e); }
        return null;
    }

    private void deliverOpen() {'''),
])
print("ok")
