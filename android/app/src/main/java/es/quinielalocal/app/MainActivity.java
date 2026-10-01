package es.quinielalocal.app;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.ContentValues;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import org.json.JSONObject;

import java.io.BufferedInputStream;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Calendar;
import java.util.Locale;
import java.util.Map;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

public class MainActivity extends Activity {
    private static final int PICK_TXT = 41;
    private static final int MAX_DOWNLOAD = 25 * 1024 * 1024;
    private WebView webView;

    @SuppressLint({"SetJavaScriptEnabled", "AddJavascriptInterface"})
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        webView = new WebView(this);
        webView.setBackgroundColor(0xff06162c);
        webView.getSettings().setJavaScriptEnabled(true);
        webView.getSettings().setDomStorageEnabled(true);
        // Los únicos ficheros locales son los recursos empaquetados dentro del APK.
        webView.getSettings().setAllowFileAccess(true);
        webView.getSettings().setAllowContentAccess(false);
        webView.setWebViewClient(new WebViewClient());
        webView.setWebChromeClient(new WebChromeClient());
        webView.addJavascriptInterface(new AndroidBridge(), "Android");
        setContentView(webView);
        webView.loadUrl("file:///android_asset/index.html");
    }

    private byte[] download(String address) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new URL(address).openConnection();
        connection.setConnectTimeout(20000);
        connection.setReadTimeout(30000);
        connection.setRequestProperty("User-Agent", "QuinielaLocal-Android/1.0");
        connection.setRequestProperty("Cache-Control", "no-cache");
        connection.setRequestProperty("Referer", "https://www.eduardolosilla.es/");
        try (InputStream input = new BufferedInputStream(connection.getInputStream());
             ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[16384];
            int count;
            while ((count = input.read(buffer)) != -1) {
                output.write(buffer, 0, count);
                if (output.size() > MAX_DOWNLOAD) throw new IllegalStateException("Descarga demasiado grande");
            }
            return output.toByteArray();
        } finally {
            connection.disconnect();
        }
    }

    private String decode(byte[] bytes) {
        String utf8 = new String(bytes, StandardCharsets.UTF_8);
        return utf8.indexOf('\ufffd') >= 0 ? new String(bytes, Charset.forName("windows-1252")) : utf8;
    }

    public class AndroidBridge {
        @JavascriptInterface public String fetchText(String url) {
            try { return decode(download(url)); }
            catch (Exception error) { return "__ERROR__" + error.getMessage(); }
        }

        @JavascriptInterface public String fetchWinData() {
            try {
                byte[] archive = download("https://www.win1x2.com/datos/actudato.zip");
                Map<String, byte[]> files = new HashMap<>();
                String newestSeason = "";
                int newestStartYear = 0;
                try (ZipInputStream zip = new ZipInputStream(new ByteArrayInputStream(archive))) {
                    ZipEntry entry;
                    while ((entry = zip.getNextEntry()) != null) {
                        if (entry.isDirectory()) continue;
                        String name = entry.getName().replace('\\', '/');
                        name = name.substring(name.lastIndexOf('/') + 1);
                        ByteArrayOutputStream output = new ByteArrayOutputStream();
                        byte[] buffer = new byte[8192];
                        int count;
                        while ((count = zip.read(buffer)) != -1) output.write(buffer, 0, count);
                        files.put(name, output.toByteArray());
                        String upper = name.toUpperCase(Locale.ROOT);
                        if (upper.matches("FEC\\d{2}-\\d{2}\\.TXT")) {
                            String season = upper.substring(3, 8);
                            int shortYear = Integer.parseInt(season.substring(0, 2));
                            int fullYear = shortYear >= 90 ? 1900 + shortYear : 2000 + shortYear;
                            if (fullYear > newestStartYear && fullYear <= Calendar.getInstance().get(Calendar.YEAR) + 1) {
                                newestStartYear = fullYear;
                                newestSeason = season;
                            }
                        }
                    }
                }
                JSONObject result = new JSONObject();
                result.put("season", newestSeason);
                for (Map.Entry<String, byte[]> item : files.entrySet()) {
                    String upper = item.getKey().toUpperCase(Locale.ROOT);
                    if (upper.equals("FEC" + newestSeason + ".TXT") ||
                        upper.equals("PRE" + newestSeason + ".TXT") ||
                        upper.equals("HOR" + newestSeason + ".TXT") ||
                        upper.equals("WEQUIPOS.TXT")) {
                        result.put(upper, decode(item.getValue()));
                    }
                }
                return result.toString();
            } catch (Exception error) {
                return "__ERROR__" + error.getMessage();
            }
        }

        @JavascriptInterface public void saveText(String filename, String text) {
            runOnUiThread(() -> {
                try {
                    ContentValues values = new ContentValues();
                    values.put(MediaStore.Downloads.DISPLAY_NAME, filename);
                    values.put(MediaStore.Downloads.MIME_TYPE, "text/plain");
                    values.put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/QuinielaLocal");
                    Uri uri = getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
                    if (uri == null) throw new IllegalStateException("No se pudo crear el archivo");
                    try (OutputStream output = getContentResolver().openOutputStream(uri)) {
                        output.write(text.getBytes(StandardCharsets.UTF_8));
                    }
                    Toast.makeText(MainActivity.this, "Guardado en Descargas/QuinielaLocal", Toast.LENGTH_LONG).show();
                } catch (Exception error) {
                    Toast.makeText(MainActivity.this, "Error al guardar: " + error.getMessage(), Toast.LENGTH_LONG).show();
                }
            });
        }

        @JavascriptInterface public void pickTextFile() {
            runOnUiThread(() -> {
                Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("text/plain");
                startActivityForResult(intent, PICK_TXT);
            });
        }

        @JavascriptInterface public void openUrl(String url) {
            runOnUiThread(() -> startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url))));
        }

        @JavascriptInterface public void notify(String message) {
            runOnUiThread(() -> Toast.makeText(MainActivity.this, message, Toast.LENGTH_LONG).show());
        }
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != PICK_TXT || resultCode != RESULT_OK || data == null || data.getData() == null) return;
        try (InputStream input = getContentResolver().openInputStream(data.getData());
             ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192];
            int count;
            while ((count = input.read(buffer)) != -1) output.write(buffer, 0, count);
            String script = "window.onImportedText(" + JSONObject.quote(decode(output.toByteArray())) + ")";
            webView.evaluateJavascript(script, null);
        } catch (Exception error) {
            Toast.makeText(this, "No se pudo leer el TXT", Toast.LENGTH_LONG).show();
        }
    }

    @Override public void onBackPressed() {
        if (webView.canGoBack()) webView.goBack(); else super.onBackPressed();
    }
}
