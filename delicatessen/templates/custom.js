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
  // Note that we need to do this after a small amount of
  // time to ensure this happens *after* things are loaded
  // on the screen!
  var delays = [0, 100, 300, 1000, 5000];
  for (i = 0; i < delays.length; i++) {
    setTimeout(fixSelectors, delays[i]);
  }
});