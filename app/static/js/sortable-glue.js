/* ─── Sortable Glue – DnD for Kanban Board ─────────────────────────
 *
 * Eine zentrale onEnd-Handler-Strategie:
 *   - onEnd feuert immer auf der SOURCE-Liste (egal ob Reorder oder Cross-Zone).
 *   - onAdd würde zusätzlich auf der DESTINATION feuern → doppelter POST.
 *     Deshalb: KEIN onAdd verwenden — nur onEnd.
 *   - Vehicle-Zonen sind pull:true, damit Mini-Items (assigned-task/msg/person)
 *     wieder aus dem Fahrzeug heraus auf Spalten oder andere Fahrzeuge gezogen
 *     werden können.
 */

(function () {
  'use strict';

  // Drag-Hover-Tab-Switch state (mobile lane switching during drag)
  let _dragging = false;
  let _hoverTabId = null;
  let _hoverStart = 0;
  const TAB_HOLD_MS = 500;

  function getIncidentId() {
    const el = document.getElementById('kanban') || document.querySelector('[data-incident-id]');
    return el ? (el.dataset.incidentId || null) : null;
  }

  function postMove(incidentId, payload) {
    const body = new URLSearchParams(payload);
    return fetch(`/einsatz/${incidentId}/karte/verschieben`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: body.toString(),
      credentials: 'same-origin',
    });
  }

  function onPointerMoveForTabSwitch(e) {
    if (!_dragging) return;
    const t = e.touches ? e.touches[0] : e;
    if (!t || t.clientX === undefined) return;
    const el = document.elementFromPoint(t.clientX, t.clientY);
    const tab = el ? el.closest('.board-tab') : null;
    if (!tab) { _hoverTabId = null; return; }
    if (tab.dataset.lane !== _hoverTabId) {
      _hoverTabId = tab.dataset.lane;
      _hoverStart = Date.now();
    } else if (Date.now() - _hoverStart > TAB_HOLD_MS && !tab.classList.contains('active')) {
      tab.click();
      _hoverStart = Date.now() + 999999;
    }
  }

  function attachDragTabSwitch() {
    if (window._dndTabSwitchAttached) return;
    window._dndTabSwitchAttached = true;
    document.addEventListener('touchmove', onPointerMoveForTabSwitch, { passive: true });
    document.addEventListener('pointermove', onPointerMoveForTabSwitch);
  }

  function destroyExistingSortable(zone) {
    if (zone._sortableInstance) {
      try { zone._sortableInstance.destroy(); } catch (e) { /* noop */ }
      zone._sortableInstance = null;
    }
  }

  // Einheitlicher onEnd-Handler für Spalten- UND Fahrzeug-Zonen
  function makeOnEnd(incidentId) {
    return function (evt) {
      _dragging = false;
      _hoverTabId = null;
      document.body.classList.remove('dnd-active');
      evt.item.removeAttribute('draggable');

      const card = evt.item;
      const kind = card.dataset.kind;
      const uid = card.dataset.uid;
      if (!uid || !kind) return;

      // Reorder ohne Positionsänderung → nichts tun
      if (evt.from === evt.to && evt.oldIndex === evt.newIndex) return;

      const toZone = evt.to;
      const position = evt.newIndex;

      // Drop auf Fahrzeug-Zone (innerhalb einer Fahrzeug-Karte)
      if (toZone.classList.contains('sortable-zone--vehicle')) {
        const vehicleId = toZone.dataset.vehicleId;
        if (!vehicleId) return;
        // Ein Fahrzeug auf ein anderes Fahrzeug zu droppen ergibt keinen Sinn
        if (kind === 'vehicle') return;
        postMove(incidentId, { kind, uid, vehicle_id: vehicleId, position });
        return;
      }

      // Drop auf Spalten-Zone
      const toColumnId = toZone.closest('[data-col-id]')?.dataset.colId;
      if (!toColumnId) return;
      postMove(incidentId, { kind, uid, column_id: toColumnId, position });
    };
  }

  function initSortable() {
    const incidentId = getIncidentId();
    if (!incidentId) return;
    attachDragTabSwitch();

    const onEnd = makeOnEnd(incidentId);
    const commonOpts = {
      group: { name: 'kanban', pull: true, put: true },
      animation: 150,
      ghostClass: 'card--ghost',
      chosenClass: 'card--chosen',
      dragClass: 'card--drag',
      delay: 150,
      touchStartThreshold: 4,
      preventOnFilter: false,
      filter: 'select,input,button,.task-check,a,label',
      onStart() {
        _dragging = true;
        document.body.classList.add('dnd-active');
      },
      onEnd,
    };

    // Spalten-Zonen (Fahrzeuge + freie Aufträge + Meldungen + Personen)
    document.querySelectorAll('.kanban-col__body.sortable-zone:not(.sortable-zone--vehicle)').forEach(zone => {
      destroyExistingSortable(zone);
      const columnId = zone.closest('[data-col-id]')?.dataset.colId;
      if (!columnId) return;

      zone._sortableInstance = new Sortable(zone, {
        ...commonOpts,
        // Spalte: ganze .card als Drag-Griff (Vehicle/Task/Message/Person-Karten)
        handle: '.card',
      });
    });

    // Fahrzeug-Drop-Zonen (innerhalb von Fahrzeug-Karten)
    document.querySelectorAll('.sortable-zone--vehicle').forEach(zone => {
      destroyExistingSortable(zone);
      const vehicleId = zone.dataset.vehicleId;
      if (!vehicleId) return;

      zone._sortableInstance = new Sortable(zone, {
        ...commonOpts,
        // Mini-Items im Fahrzeug haben keine .card-Klasse — kein handle setzen,
        // damit das ganze Mini-Item-Element draggable ist.
        handle: undefined,
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSortable);
  } else {
    initSortable();
  }

  // Re-init nach HTMX-Swaps (Board-Reload, OOB-Swaps)
  document.body.addEventListener('htmx:afterSwap', () => setTimeout(initSortable, 50));
  document.body.addEventListener('htmx:oobAfterSwap', () => setTimeout(initSortable, 50));
  document.body.addEventListener('htmx:load', () => setTimeout(initSortable, 50));
})();
