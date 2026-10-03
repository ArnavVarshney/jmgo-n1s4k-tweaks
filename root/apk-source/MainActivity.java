package com.exec.cmd;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.ServiceConnection;
import android.os.Bundle;
import android.os.IBinder;
import android.os.Parcel;
import android.util.Log;
import java.io.BufferedReader;
import java.io.InputStreamReader;

public class MainActivity extends Activity {
    static final String TAG = "ExecCmd";
    static final int TRANSACTION_execCommand = 10;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        String cmd = getIntent().getStringExtra("cmd");
        if (cmd == null || cmd.isEmpty()) cmd = "id";
        final String command = cmd;

        // Check if "direct" mode — run via Runtime.exec directly in THIS process
        // (for commands that need output capture)
        String mode = getIntent().getStringExtra("mode");
        if ("direct".equals(mode)) {
            new Thread(() -> {
                try {
                    Log.i(TAG, "DIRECT exec: " + command);
                    Process p = Runtime.getRuntime().exec(command.split(" "));
                    BufferedReader br = new BufferedReader(new InputStreamReader(p.getInputStream()));
                    BufferedReader er = new BufferedReader(new InputStreamReader(p.getErrorStream()));
                    String line;
                    StringBuilder sb = new StringBuilder();
                    while ((line = br.readLine()) != null) {
                        sb.append(line).append("\n");
                        Log.i(TAG, "OUT: " + line);
                    }
                    while ((line = er.readLine()) != null) {
                        Log.e(TAG, "ERR: " + line);
                    }
                    p.waitFor();
                    Log.i(TAG, "EXIT: " + p.exitValue());
                } catch (Exception e) {
                    Log.e(TAG, "DIRECT ERROR: " + e);
                }
                finish();
            }).start();
            return;
        }

        // Default: use SettingService.execCommand (runs as system user)
        Log.i(TAG, "CMD via SettingService: " + command);
        Intent intent = new Intent();
        intent.setComponent(new ComponentName(
            "com.jmgo.systemapi",
            "com.jmgo.systemapi.SettingService"));

        bindService(intent, new ServiceConnection() {
            public void onServiceConnected(ComponentName name, IBinder binder) {
                try {
                    Log.i(TAG, "CONNECTED");
                    Parcel data = Parcel.obtain();
                    Parcel reply = Parcel.obtain();
                    data.writeInterfaceToken("com.jmgo.systemapi.ISettings");
                    data.writeString(command);
                    boolean ok = binder.transact(TRANSACTION_execCommand, data, reply, 0);
                    Log.i(TAG, "transact=" + ok);
                    if (ok) {
                        reply.readException();
                        String result = reply.readString();
                        Log.i(TAG, "RESULT: " + result);
                    }
                    data.recycle();
                    reply.recycle();
                } catch (Exception e) {
                    Log.e(TAG, "ERROR: " + e);
                }
                unbindService(this);
                finish();
            }
            public void onServiceDisconnected(ComponentName name) {}
        }, Context.BIND_AUTO_CREATE);
    }
}
