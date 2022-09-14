package a2dp.Vol;

import android.app.Service;
import android.content.Intent;
import android.content.SharedPreferences;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Bundle;
import android.os.CountDownTimer;
import android.os.Environment;
import android.os.IBinder;
import android.preference.PreferenceManager;
import android.support.v4.app.ActivityCompat;
import android.text.format.DateUtils;
import android.util.Log;
import android.widget.Toast;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.net.URLEncoder;
import java.text.DecimalFormat;
import java.util.List;

public class StoreLoc extends Service {
    private static final String LOG_TAG = "A2DP_Volume";
    public static final String PREFS_NAME = "btVol";
    private DeviceDB DB;
    float MAX_ACC = 20.0f;
    long MAX_TIME = 10000;
    String a2dpDir = "";
    private MyApplication application;
    btDevice btdConn;
    Long dtime = null;
    int formatFlags;
    int formatFlags2;
    boolean gpsEnabled = false;
    Location l = null;
    Location l3 = null;
    Location l4 = null;
    boolean local;
    LocationListener locationListener = new LocationListener() {
        /* class a2dp.Vol.StoreLoc.AnonymousClass2 */

        public void onLocationChanged(Location location) {
            StoreLoc.this.grabGPS();
        }

        public void onProviderEnabled(String provider) {
        }

        public void onProviderDisabled(String provider) {
        }

        public void onStatusChanged(String provider, int status, Bundle extras) {
        }
    };
    private LocationManager locationManager;
    SharedPreferences preferences;
    private boolean toasts = true;
    private boolean useNet = true;
    private boolean usePass = false;

    public IBinder onBind(Intent intent) {
        return null;
    }

    public int onStartCommand(Intent intent, int flags, int startId) {
        try {
            this.preferences = PreferenceManager.getDefaultSharedPreferences(this.application);
            this.toasts = this.preferences.getBoolean("toasts", true);
            this.usePass = this.preferences.getBoolean("usePassive", false);
            this.useNet = this.preferences.getBoolean("useNetwork", true);
            this.MAX_TIME = new Long(this.preferences.getString("gpsTime", "15000")).longValue();
            this.MAX_ACC = new Float(this.preferences.getString("gpsDistance", "10")).floatValue();
            this.local = this.preferences.getBoolean("useLocalStorage", false);
            if (this.local) {
                this.a2dpDir = getFilesDir().toString();
            } else {
                this.a2dpDir = Environment.getExternalStorageDirectory() + "/A2DPVol";
            }
        } catch (NumberFormatException e) {
            this.MAX_ACC = 10.0f;
            this.MAX_TIME = 15000;
            Toast.makeText(this, "prefs failed to load. " + e.getMessage(), 1).show();
            e.printStackTrace();
            Log.e(LOG_TAG, "prefs failed to load " + e.getMessage());
        }
        this.l = null;
        this.l3 = null;
        this.l4 = null;
        try {
            this.btdConn = this.DB.getBTD(intent.getStringExtra("device"));
        } catch (Exception e2) {
            Toast.makeText(this, "Location service failed to start. " + e2.getMessage(), 1).show();
            stopSelf();
            e2.printStackTrace();
        }
        this.locationManager = (LocationManager) getSystemService("location");
        this.dtime = Long.valueOf(System.currentTimeMillis());
        registerListeners();
        if (this.MAX_TIME > 0) {
            new CountDownTimer(this.MAX_TIME, 5000) {
                /* class a2dp.Vol.StoreLoc.AnonymousClass1 */

                public void onTick(long millisUntilFinished) {
                    if (StoreLoc.this.toasts) {
                        Toast.makeText(StoreLoc.this.application, "Time left: " + ((20 + millisUntilFinished) / 1000), 1).show();
                    }
                }

                public void onFinish() {
                    StoreLoc.this.clearLoc(true);
                }
            }.start();
        }
        return super.onStartCommand(intent, flags, startId);
    }

    public void onCreate() {
        this.application = (MyApplication) getApplication();
        this.DB = new DeviceDB(this.application);
        this.formatFlags = 524288;
        this.formatFlags |= 16;
        this.formatFlags |= 1;
        this.formatFlags |= 4;
    }

    public void onDestroy() {
        this.DB.getDb().close();
        if (this.locationListener != null) {
            try {
                if (ActivityCompat.checkSelfPermission(this, "android.permission.ACCESS_FINE_LOCATION") == 0 || ActivityCompat.checkSelfPermission(this, "android.permission.ACCESS_COARSE_LOCATION") == 0) {
                    this.locationManager.removeUpdates(this.locationListener);
                } else {
                    return;
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
        super.onDestroy();
    }

    /* access modifiers changed from: protected */
    @Override // java.lang.Object
    public void finalize() throws Throwable {
        this.DB.getDb().close();
        if (this.locationListener != null) {
            try {
                if (ActivityCompat.checkSelfPermission(this, "android.permission.ACCESS_FINE_LOCATION") == 0 || ActivityCompat.checkSelfPermission(this, "android.permission.ACCESS_COARSE_LOCATION") == 0) {
                    this.locationManager.removeUpdates(this.locationListener);
                } else {
                    return;
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
        super.finalize();
    }

    /* access modifiers changed from: package-private */
    public void grabGPS() {
        String urlStr;
        String urlStr2;
        String car = "My Car";
        LocationManager lm = (LocationManager) getSystemService("location");
        List<String> providers = lm.getProviders(true);
        long deltat = 9999999;
        float oldacc = 1.0E8f;
        float bestacc = 1.0E8f;
        if (this.l4 != null && this.l4.hasAccuracy()) {
            bestacc = this.l4.getAccuracy();
        }
        if (this.l3 != null && this.l3.hasAccuracy()) {
            oldacc = this.l3.getAccuracy();
        }
        if (this.l != null) {
            long olddt = System.currentTimeMillis() - this.l.getTime();
        }
        try {
            if (!providers.isEmpty()) {
                for (int i = providers.size() - 1; i >= 0; i--) {
                    if (ActivityCompat.checkSelfPermission(this, "android.permission.ACCESS_FINE_LOCATION") == 0 || ActivityCompat.checkSelfPermission(this, "android.permission.ACCESS_COARSE_LOCATION") == 0) {
                        Location l2 = lm.getLastKnownLocation(providers.get(i));
                        if (l2 != null) {
                            if (l2.hasAccuracy()) {
                                float acc = l2.getAccuracy();
                                if (acc < oldacc) {
                                    this.l3 = l2;
                                    oldacc = acc;
                                }
                                if (acc < bestacc && l2.getTime() > this.dtime.longValue() - this.MAX_TIME) {
                                    this.l4 = l2;
                                    bestacc = acc;
                                }
                            }
                            deltat = System.currentTimeMillis() - l2.getTime();
                            if (deltat < deltat) {
                                this.l = l2;
                            }
                        }
                    } else {
                        return;
                    }
                }
                if (!(this.locationListener == null || this.l4 == null)) {
                    float x = this.l4.getAccuracy();
                    if (x < this.MAX_ACC && x > 0.0f && System.currentTimeMillis() - this.l4.getTime() < this.MAX_TIME) {
                        clearLoc(true);
                    }
                }
                DecimalFormat df = new DecimalFormat("#.#");
                if (this.btdConn != null) {
                    car = this.btdConn.getDesc2();
                }
                if (this.l4 != null) {
                    String locTime = DateUtils.formatDateTime(this.application, this.l4.getTime(), this.formatFlags);
                    try {
                        urlStr2 = URLEncoder.encode(this.l4.getLatitude() + "," + this.l4.getLongitude() + "(" + car + " " + locTime + " acc=" + df.format((double) this.l4.getAccuracy()) + ")", "UTF-8");
                    } catch (UnsupportedEncodingException e1) {
                        urlStr2 = URLEncoder.encode(this.l4.getLatitude() + "," + this.l4.getLongitude() + "(" + car + " " + locTime + " acc=" + df.format((double) this.l4.getAccuracy()) + ")");
                        e1.printStackTrace();
                    }
                    try {
                        FileOutputStream fos = openFileOutput("My_Last_Location", 1);
                        fos.write(("http://maps.google.com/maps?q=" + urlStr2).getBytes());
                        fos.close();
                    } catch (FileNotFoundException e) {
                        Toast.makeText(this.application, "FileNotFound", 1).show();
                        e.printStackTrace();
                    } catch (IOException e2) {
                        Toast.makeText(this.application, "IOException", 1).show();
                        e2.printStackTrace();
                    }
                }
                if (this.l3 != null) {
                    String locTime2 = DateUtils.formatDateTime(this.application, this.l3.getTime(), this.formatFlags);
                    try {
                        urlStr = URLEncoder.encode(this.l3.getLatitude() + "," + this.l3.getLongitude() + "(" + car + " " + locTime2 + " acc=" + df.format((double) this.l3.getAccuracy()) + ")", "UTF-8");
                    } catch (UnsupportedEncodingException e12) {
                        urlStr = URLEncoder.encode(this.l3.getLatitude() + "," + this.l3.getLongitude() + "(" + car + " " + locTime2 + " acc=" + df.format((double) this.l3.getAccuracy()) + ")");
                        e12.printStackTrace();
                    }
                    try {
                        FileOutputStream fos2 = openFileOutput("My_Last_Location2", 1);
                        fos2.write(("http://maps.google.com/maps?q=" + urlStr).getBytes());
                        fos2.close();
                    } catch (FileNotFoundException e3) {
                        Toast.makeText(this.application, "FileNotFound", 1).show();
                        e3.printStackTrace();
                    } catch (IOException e4) {
                        Toast.makeText(this.application, "IOException", 1).show();
                        e4.printStackTrace();
                    }
                }
            }
        } catch (Exception e5) {
        }
    }

    /* access modifiers changed from: private */
    /* access modifiers changed from: public */
    private void clearLoc(boolean doGps) {
        String temp;
        String temp2;
        String temp3;
        String urlStr;
        String urlStr2;
        String urlStr3;
        if (ActivityCompat.checkSelfPermission(this, "android.permission.ACCESS_FINE_LOCATION") == 0 || ActivityCompat.checkSelfPermission(this, "android.permission.ACCESS_COARSE_LOCATION") == 0) {
            this.locationManager.removeUpdates(this.locationListener);
            String car = "My Car";
            DecimalFormat df = new DecimalFormat("#.#");
            if (this.btdConn != null) {
                car = this.btdConn.getDesc2();
            }
            try {
                File exportDir = new File(this.a2dpDir);
                if (!exportDir.exists()) {
                    exportDir.mkdirs();
                }
                File file = new File(exportDir, car.replaceAll(" ", "_") + ".html");
                if (this.l4 != null) {
                    String locTime = DateUtils.formatDateTime(this.application, this.l4.getTime(), this.formatFlags);
                    try {
                        urlStr3 = URLEncoder.encode(this.l4.getLatitude() + "," + this.l4.getLongitude() + "(" + car + " " + locTime + " acc=" + df.format((double) this.l4.getAccuracy()) + ")", "UTF-8");
                    } catch (Exception e) {
                        urlStr3 = URLEncoder.encode(this.l4.getLatitude() + "," + this.l4.getLongitude() + "(" + car + " " + locTime + " acc=" + df.format((double) this.l4.getAccuracy()) + ")");
                        e.printStackTrace();
                    }
                    temp = "<hr /><bold><a href=\"http://maps.google.com/maps?q=" + urlStr3 + "\">" + car + "</a></bold> Best Location<br>Time: " + locTime + "<br>Location type: " + this.l4.getProvider() + "<br>Accuracy: " + this.l4.getAccuracy() + " meters<br>Elevation: " + this.l4.getAltitude() + " meters<br>Lattitude: " + this.l4.getLatitude() + "<br>Longitude: " + this.l4.getLongitude();
                } else {
                    temp = "No Best Location Captured " + DateUtils.formatDateTime(this.application, this.dtime.longValue(), this.formatFlags) + "<br>";
                }
                if (this.l3 != null) {
                    String locTime2 = DateUtils.formatDateTime(this.application, this.l3.getTime(), this.formatFlags);
                    try {
                        urlStr2 = URLEncoder.encode(this.l3.getLatitude() + "," + this.l3.getLongitude() + "(" + car + " " + locTime2 + " acc=" + df.format((double) this.l3.getAccuracy()) + ")", "UTF-8");
                    } catch (Exception e2) {
                        urlStr2 = URLEncoder.encode(this.l3.getLatitude() + "," + this.l3.getLongitude() + "(" + car + " " + locTime2 + " acc=" + df.format((double) this.l3.getAccuracy()) + ")");
                        e2.printStackTrace();
                    }
                    temp2 = temp + "<hr /><bold><a href=\"http://maps.google.com/maps?q=" + urlStr2 + "\">" + car + "</a></bold> Most Accurate Location<br>Time: " + locTime2 + "<br>Location type: " + this.l3.getProvider() + "<br>Accuracy: " + this.l3.getAccuracy() + " meters<br>Elevation: " + this.l3.getAltitude() + " meters<br>Lattitude: " + this.l3.getLatitude() + "<br>Longitude: " + this.l3.getLongitude();
                } else {
                    temp2 = temp + "No Most Accurate Location Captured " + DateUtils.formatDateTime(this.application, this.dtime.longValue(), this.formatFlags) + "<br>";
                }
                if (this.l != null) {
                    String locTime3 = DateUtils.formatDateTime(this.application, this.l.getTime(), this.formatFlags);
                    try {
                        urlStr = URLEncoder.encode(this.l.getLatitude() + "," + this.l.getLongitude() + "(" + car + " " + locTime3 + " acc=" + df.format((double) this.l.getAccuracy()) + ")", "UTF-8");
                    } catch (Exception e3) {
                        urlStr = URLEncoder.encode(this.l.getLatitude() + "," + this.l.getLongitude() + "(" + car + " " + locTime3 + " acc=" + df.format((double) this.l.getAccuracy()) + ")");
                        e3.printStackTrace();
                    }
                    temp3 = temp2 + "<hr /><bold><a href=\"http://maps.google.com/maps?q=" + urlStr + "\">" + car + "</a></bold> Most Recent Location<br>Time: " + locTime3 + "<br>Location type: " + this.l.getProvider() + "<br>Accuracy: " + this.l.getAccuracy() + " meters<br>Elevation: " + this.l.getAltitude() + " meters<br>Lattitude: " + this.l.getLatitude() + "<br>Longitude: " + this.l.getLongitude();
                } else {
                    temp3 = temp2 + "No Most Recent Location Captured " + DateUtils.formatDateTime(this.application, this.dtime.longValue(), this.formatFlags) + "<br>";
                }
                if (!this.gpsEnabled) {
                    temp3 = temp3 + "<br>GPS was not enabled";
                }
                if (this.local) {
                    FileOutputStream fos = openFileOutput(file.getName(), 1);
                    fos.write(temp3.getBytes());
                    fos.close();
                } else {
                    FileOutputStream fos2 = new FileOutputStream(file);
                    fos2.write(temp3.getBytes());
                    fos2.close();
                }
            } catch (FileNotFoundException e4) {
                Toast.makeText(this.application, "FileNotFound", 1).show();
                e4.printStackTrace();
                Log.e(LOG_TAG, "Error " + e4.getMessage());
            } catch (IOException e5) {
                Toast.makeText(this.application, "IOException", 1).show();
                e5.printStackTrace();
                Log.e(LOG_TAG, "Error " + e5.getMessage());
            }
            this.l = null;
            this.l3 = null;
            this.l4 = null;
            this.btdConn = null;
            stopSelf();
        }
    }

    private void registerListeners() {
        if (!this.locationManager.isProviderEnabled("gps")) {
            this.gpsEnabled = false;
        } else if (ActivityCompat.checkSelfPermission(this, "android.permission.ACCESS_FINE_LOCATION") == 0 || ActivityCompat.checkSelfPermission(this, "android.permission.ACCESS_COARSE_LOCATION") == 0) {
            this.locationManager.requestLocationUpdates("gps", 0, 0.0f, this.locationListener);
            this.gpsEnabled = true;
        } else {
            return;
        }
        if (this.useNet && this.locationManager.isProviderEnabled("network")) {
            this.locationManager.requestLocationUpdates("network", 0, 0.0f, this.locationListener);
        }
        if (this.usePass && this.locationManager.isProviderEnabled("passive")) {
            this.locationManager.requestLocationUpdates("passive", 0, 0.0f, this.locationListener);
        }
    }
}
