// Alpine.js component for the media gallery lightbox.
// Usage in template: x-data="lightboxState()" @keydown.escape.window="close()"
// Trigger: @click="show(idx)" on each image/video card.
// Items are read from window._lbItems (set by gallery template).
function lightboxState() {
  return {
    open: false,
    items: [],
    current: 0,

    show(idx) {
      this.items = window._lbItems || [];
      this.current = idx;
      this.open = true;
      document.body.style.overflow = 'hidden';
    },

    close() {
      this.open = false;
      document.body.style.overflow = '';
    },

    prev() {
      if (this.current > 0) this.current--;
    },

    next() {
      if (this.current < this.items.length - 1) this.current++;
    },

    get item() {
      return this.items[this.current] || null;
    },
  };
}
