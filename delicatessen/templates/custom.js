function fixSelectors() {
  items = document.getElementsByName('deli-selector');
  for (i = 0; i < items.length; i++) {
    items[i].size = '8';
  }
}

$(document).ready(function() {
  // Once the page loads, turn the drop-down menus into
  // lists where all items are visible. This is a hack,
  // since I couldn't figure out how to set the "size"
  // property of the "select" element within Bokeh or CSS.
  setTimeout(fixSelectors, 100);
  setTimeout(fixSelectors, 300);
  setTimeout(fixSelectors, 500);
  setTimeout(fixSelectors, 1000);
});