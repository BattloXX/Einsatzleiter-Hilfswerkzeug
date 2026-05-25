// PWA-Install-Helfer.
// Faengt `beforeinstallprompt` ab und blendet "App installieren"-Eintraege
// im Topnav + Mobile-Menue sichtbar. iOS/Safari (kein BIP) -> Hinweis-Dialog.
//
// Eintraege im DOM:
//   .pwa-install-btn (button oder a) - werden sichtbar gemacht
//   .pwa-install-ios (button oder a) - nur fuer iOS-Safari sichtbar
// Beim Klick auf .pwa-install-btn -> prompt().
// Beim Klick auf .pwa-install-ios -> Modal-Hinweis.

(function () {
  let deferredPrompt = null;

  function isStandalone() {
    return (
      window.matchMedia && window.matchMedia('(display-mode: standalone)').matches
    ) || window.navigator.standalone === true;
  }

  function isIosSafari() {
    const ua = window.navigator.userAgent || '';
    const isIos = /iPad|iPhone|iPod/.test(ua) && !window.MSStream;
    const isSafari = /Safari/.test(ua) && !/CriOS|FxiOS|EdgiOS/.test(ua);
    return isIos && isSafari;
  }

  function show(selector) {
    document.querySelectorAll(selector).forEach((el) => {
      el.style.removeProperty('display');
      el.classList.remove('hidden');
      el.removeAttribute('hidden');
    });
  }

  function hide(selector) {
    document.querySelectorAll(selector).forEach((el) => {
      el.style.display = 'none';
    });
  }

  function refreshVisibility() {
    if (isStandalone()) {
      hide('.pwa-install-btn');
      hide('.pwa-install-ios');
      return;
    }
    if (deferredPrompt) {
      show('.pwa-install-btn');
      hide('.pwa-install-ios');
    } else if (isIosSafari()) {
      show('.pwa-install-ios');
      hide('.pwa-install-btn');
    } else {
      // Kein Prompt verfuegbar und kein iOS -> versteckt lassen, sonst frustriert.
      hide('.pwa-install-btn');
      hide('.pwa-install-ios');
    }
  }

  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    refreshVisibility();
  });

  window.addEventListener('appinstalled', () => {
    deferredPrompt = null;
    hide('.pwa-install-btn');
    hide('.pwa-install-ios');
  });

  window.installPwa = async function () {
    if (!deferredPrompt) return;
    try {
      deferredPrompt.prompt();
      await deferredPrompt.userChoice;
    } catch (e) {
      console.warn('[pwa-install] prompt failed', e);
    } finally {
      deferredPrompt = null;
      refreshVisibility();
    }
  };

  window.showIosInstallHint = function () {
    const dlg = document.getElementById('iosInstallHint');
    if (dlg && typeof dlg.showModal === 'function') {
      if (dlg.open) dlg.close();
      dlg.showModal();
    } else {
      alert(
        'iPhone/iPad: Im Safari unten auf "Teilen" tippen → ' +
        '"Zum Home-Bildschirm" wählen, um die App zu installieren.'
      );
    }
  };

  document.addEventListener('DOMContentLoaded', () => {
    refreshVisibility();
    document.querySelectorAll('.pwa-install-btn').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        window.installPwa();
      });
    });
    document.querySelectorAll('.pwa-install-ios').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        window.showIosInstallHint();
      });
    });
  });
})();
