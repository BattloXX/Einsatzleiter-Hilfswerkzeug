// In-App-Lightbox fuer Bilder / PDFs / Videos.
// Aufruf: openMediaViewer(url, kind, filename)
//   kind: "image" | "pdf" | "video"
// Schliessen: ESC oder Klick auf x, Klick auf den Backdrop ausserhalb des Inhalts.
//
// Mehrere geoeffnete <dialog>s sind erlaubt - der Browser stackt sie korrekt
// im Top-Layer. Wir bauen den Viewer als Sibling von <body>, nicht innerhalb
// eines bereits offenen Modals.

(function () {
  function ensureViewer() {
    let dlg = document.getElementById('mediaViewer');
    if (dlg) return dlg;
    dlg = document.createElement('dialog');
    dlg.id = 'mediaViewer';
    dlg.className = 'media-viewer';
    dlg.innerHTML = `
      <div class="media-viewer__toolbar">
        <span class="media-viewer__name" id="mediaViewerName"></span>
        <div class="media-viewer__actions">
          <a id="mediaViewerDownload" href="#" download class="btn btn--secondary btn--sm" title="Datei herunterladen">⬇ Download</a>
          <button type="button" class="media-viewer__close" aria-label="Schliessen">×</button>
        </div>
      </div>
      <div class="media-viewer__content" id="mediaViewerContent"></div>
    `;
    document.body.appendChild(dlg);
    // Schliess-Button
    dlg.querySelector('.media-viewer__close').addEventListener('click', closeMediaViewer);
    // Klick auf den Dialog (= auf das Backdrop ausserhalb des Inhalts) schliesst.
    dlg.addEventListener('click', (e) => {
      if (e.target === dlg) closeMediaViewer();
    });
    // ESC schliesst (zusaetzlich zum Browser-Default fuer <dialog>).
    dlg.addEventListener('cancel', (e) => {
      e.preventDefault();
      closeMediaViewer();
    });
    return dlg;
  }

  window.openMediaViewer = function (url, kind, filename) {
    try {
      const dlg = ensureViewer();
      const content = dlg.querySelector('#mediaViewerContent');
      const dl = dlg.querySelector('#mediaViewerDownload');
      const name = dlg.querySelector('#mediaViewerName');
      content.innerHTML = '';

      if (kind === 'image') {
        const img = document.createElement('img');
        img.src = url;
        img.alt = filename || '';
        img.className = 'media-viewer__image';
        content.appendChild(img);
      } else if (kind === 'pdf') {
        const iframe = document.createElement('iframe');
        iframe.src = url;
        iframe.className = 'media-viewer__iframe';
        iframe.setAttribute('title', filename || 'PDF');
        // Falls der Browser PDF nicht inline rendern kann: Fallback-Link einblenden
        iframe.addEventListener('error', () => {
          content.innerHTML =
            '<div style="color:#fff;padding:24px;text-align:center;">' +
            'PDF kann nicht eingebettet werden. ' +
            '<a href="' + url + '" target="_blank" rel="noopener" style="color:#9ec5ff;">' +
            'In neuem Tab öffnen</a>.</div>';
        });
        content.appendChild(iframe);
      } else if (kind === 'video') {
        const video = document.createElement('video');
        video.src = url;
        video.controls = true;
        video.autoplay = true;
        video.preload = 'metadata';
        video.playsInline = true;
        video.className = 'media-viewer__video';
        content.appendChild(video);
      } else {
        content.textContent = 'Unbekannter Dateityp.';
      }

      // Download-Link nutzt ?download=1 -> Server schickt Content-Disposition: attachment
      const dlUrl = url + (url.includes('?') ? '&' : '?') + 'download=1';
      dl.href = dlUrl;
      dl.setAttribute('download', filename || '');
      name.textContent = filename || '';

      if (dlg.open) dlg.close();
      dlg.showModal();
    } catch (err) {
      // Falls showModal scheitert (z. B. weil schon ein Dialog im Top-Layer ist und
      // der Browser den zweiten verweigert), fallen wir auf Tab-Open zurueck.
      console.error('[media-viewer] open failed:', err);
      window.open(url, '_blank', 'noopener');
    }
  };

  window.closeMediaViewer = function () {
    const dlg = document.getElementById('mediaViewer');
    if (!dlg) return;
    const content = dlg.querySelector('#mediaViewerContent');
    // Video/Audio anhalten, sonst spielt's im Hintergrund weiter.
    content.querySelectorAll('video,audio').forEach((el) => {
      try { el.pause(); } catch (e) { /* ignore */ }
    });
    content.innerHTML = '';
    if (dlg.open) dlg.close();
  };
})();
