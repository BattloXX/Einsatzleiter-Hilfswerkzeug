/**
 * native-bridge.js – Capacitor ↔ Web Bridge für einsatzleiter.cloud
 *
 * Erkennt ob die App in Capacitor läuft und stellt window.ELNative bereit.
 * In der reinen PWA sind alle Funktionen No-Ops oder fallen auf Web-APIs zurück,
 * sodass die Web-App weiterhin voll funktionsfähig bleibt.
 *
 * Verfügbare Funktionen:
 *   ELNative.keepAwake(on)          – Bildschirm aktiv halten (oder freigeben)
 *   ELNative.startLocation()        – Hintergrund-GPS starten
 *   ELNative.stopLocation()         – Hintergrund-GPS stoppen
 *   ELNative.scanQr(onResult)       – QR-Scanner öffnen; onResult(url) bei Erfolg
 *   ELNative.isNative               – true wenn in Capacitor-App
 */
(function () {
  'use strict';

  const isCapacitor = !!(window.Capacitor && window.Capacitor.isNative);

  // ─── FCM-Token registrieren ─────────────────────────────────────────────────
  // Wird automatisch beim ersten Laden nach Login aufgerufen.
  async function _registerFcmToken() {
    if (!isCapacitor) return;
    try {
      const { PushNotifications } = window.Capacitor.Plugins;
      if (!PushNotifications) return;

      // Berechtigung anfordern
      const perm = await PushNotifications.requestPermissions();
      if (perm.receive !== 'granted') return;

      await PushNotifications.register();
      PushNotifications.addListener('registration', async (reg) => {
        try {
          await fetch('/api/v1/device/fcm-token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
            body: JSON.stringify({ token: reg.value, platform: 'android' }),
          });
        } catch (e) {
          console.warn('[ELNative] FCM-Token-Registrierung fehlgeschlagen:', e);
        }
      });

      // Push-Notification Tap → URL öffnen
      PushNotifications.addListener('pushNotificationActionPerformed', (action) => {
        const url = action?.notification?.data?.url;
        if (url) window.location.href = url;
      });
    } catch (e) {
      console.warn('[ELNative] PushNotifications Fehler:', e);
    }
  }

  // ─── Keep-Awake ─────────────────────────────────────────────────────────────
  function keepAwake(on) {
    if (!isCapacitor) {
      // PWA-Fallback: Screen Wake Lock API
      if (on) {
        if ('wakeLock' in navigator) {
          navigator.wakeLock.request('screen').catch(() => {});
        }
      }
      return;
    }
    try {
      const { KeepAwake } = window.Capacitor.Plugins;
      if (!KeepAwake) return;
      if (on) KeepAwake.keepAwake();
      else KeepAwake.allowSleep();
    } catch (e) {
      console.warn('[ELNative] KeepAwake Fehler:', e);
    }
  }

  // ─── Standort-Tracking ──────────────────────────────────────────────────────
  let _locationWatch = null;

  function startLocation() {
    if (!isCapacitor) return;
    try {
      const { BackgroundGeolocation } = window.Capacitor.Plugins;
      if (!BackgroundGeolocation) return;
      BackgroundGeolocation.addWatcher(
        {
          backgroundMessage: 'Standort wird im Einsatz übermittelt.',
          backgroundTitle: 'einsatzleiter.cloud',
          requestPermissions: true,
          stale: false,
          distanceFilter: 20, // Meter Mindestbewegung
        },
        function callback(loc, err) {
          if (err) return;
          // Position ans Backend übermitteln (fire-and-forget)
          fetch('/api/v1/device/location', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
            body: JSON.stringify({ lat: loc.latitude, lng: loc.longitude, accuracy: loc.accuracy }),
          }).catch(() => {});
        },
      ).then((id) => { _locationWatch = id; });
    } catch (e) {
      console.warn('[ELNative] BackgroundGeolocation Fehler:', e);
    }
  }

  function stopLocation() {
    if (!isCapacitor || !_locationWatch) return;
    try {
      const { BackgroundGeolocation } = window.Capacitor.Plugins;
      if (BackgroundGeolocation && _locationWatch) {
        BackgroundGeolocation.removeWatcher({ id: _locationWatch });
        _locationWatch = null;
      }
    } catch (e) {
      console.warn('[ELNative] stopLocation Fehler:', e);
    }
  }

  // ─── QR-Scanner ─────────────────────────────────────────────────────────────
  async function scanQr(onResult) {
    if (!isCapacitor) {
      // PWA-Fallback: nicht verfügbar
      console.warn('[ELNative] QR-Scanner nur in nativer App verfügbar');
      return;
    }
    try {
      const { BarcodeScanner } = window.Capacitor.Plugins;
      if (!BarcodeScanner) return;
      const result = await BarcodeScanner.scan();
      if (result && result.content && typeof onResult === 'function') {
        onResult(result.content);
      }
    } catch (e) {
      console.warn('[ELNative] QR-Scanner Fehler:', e);
    }
  }

  // ─── Dienst-Status pollen & Tracking automatisch steuern ────────────────────
  async function _pollDutyState() {
    if (!isCapacitor) return;
    try {
      const resp = await fetch('/api/v1/device/duty-state', {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });
      if (!resp.ok) return;
      const data = await resp.json();
      if (data.should_track) startLocation();
      else stopLocation();
    } catch (_) {}
  }

  // Alle 60 Sekunden prüfen (nur wenn Tab sichtbar)
  setInterval(() => {
    if (document.visibilityState === 'visible') _pollDutyState();
  }, 60_000);

  // ─── Initialisierung ─────────────────────────────────────────────────────────
  if (isCapacitor) {
    // FCM registrieren sobald DOM bereit ist
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', _registerFcmToken);
    } else {
      _registerFcmToken();
    }
    // Initiale Dienst-Status-Prüfung
    _pollDutyState();
  }

  // ─── Öffentliche API ─────────────────────────────────────────────────────────
  window.ELNative = {
    isNative: isCapacitor,
    keepAwake,
    startLocation,
    stopLocation,
    scanQr,
  };
})();
