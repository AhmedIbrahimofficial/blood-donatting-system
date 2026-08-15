/**
 * Firebase client-side initialisation.
 *
 * Har value Firebase Console se aati hai:
 *   https://console.firebase.google.com → Project Settings → Your Apps → Web
 *
 * Values ko lifeline-connect/.env mein daalo:
 *   VITE_FIREBASE_API_KEY=...
 *   VITE_FIREBASE_AUTH_DOMAIN=...
 *   VITE_FIREBASE_PROJECT_ID=...
 *   VITE_FIREBASE_APP_ID=...
 */
import { initializeApp, getApps } from "firebase/app";
import {
  getAuth,
  GoogleAuthProvider,
  signInWithPopup,
  signOut as firebaseSignOut,
  type UserCredential,
} from "firebase/auth";

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID,
};

// Prevent duplicate initialisation in dev (HMR)
const app = getApps().length ? getApps()[0] : initializeApp(firebaseConfig);
export const auth = getAuth(app);

const googleProvider = new GoogleAuthProvider();
googleProvider.setCustomParameters({ prompt: "select_account" });

// ---------------------------------------------------------------------------
// Sign in with Google popup → returns Firebase UserCredential
// ---------------------------------------------------------------------------
export async function signInWithGoogle(): Promise<UserCredential> {
  return signInWithPopup(auth, googleProvider);
}

// ---------------------------------------------------------------------------
// Sign out from Firebase
// ---------------------------------------------------------------------------
export async function signOutGoogle(): Promise<void> {
  return firebaseSignOut(auth);
}
