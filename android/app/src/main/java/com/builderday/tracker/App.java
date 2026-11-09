package com.builderday.tracker;

import android.app.Application;

/** Loads the saved routine before any alarm, service or screen runs. */
public class App extends Application {
    @Override
    public void onCreate() {
        super.onCreate();
        Schedule.load(this);
    }
}
