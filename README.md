# Builder Day Tracker

A daily tracker for the Full-Time Builder Day (Years 1–3 template): wake time, time taken per block,
rep counters, personal records, the Daily Five, and a weekly score.

It's one static page (`index.html`). Sign-in and syncing across devices use Firebase
(Google sign-in + Firestore). Until Firebase is configured, the page saves to the browser only.

## Set up syncing (one time)

1. Go to https://console.firebase.google.com and click **Create a project** (Google Analytics not needed).
2. **Build → Authentication → Get started → Sign-in method → Google → Enable**, pick a support email, and save.
3. **Authentication → Settings → Authorized domains → Add domain:** `dinduac1.github.io`
4. **Build → Firestore Database → Create database** → production mode → pick a location near you.
5. In Firestore, open the **Rules** tab, paste the contents of `firestore.rules`, and click **Publish**.
6. **Project settings (gear icon) → Your apps → Web (`</>`)** → register an app (no hosting needed).
   Copy the `firebaseConfig` values into `firebase-config.js`.
7. Commit and push. GitHub Pages redeploys in about a minute.

The config values in `firebase-config.js` are public by design. Your data is protected by
`firestore.rules`: each signed-in person can only read and write their own tracker.

## Where data lives

- Firestore: `users/{uid}/tracker/day-YYYY-MM-DD` (one doc per day) and `users/{uid}/tracker/settings`
  (rep counters, workout plan, record directions).
- Each browser also keeps an offline copy, so the page still works without a connection and syncs when it's back.
