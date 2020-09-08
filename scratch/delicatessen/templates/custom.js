$(document).ready(function() {
  setTimeout(function() {

    items = document.getElementsByName('deli-selector');
    console.log(items);
    console.log(items.length);
    for (i = 0; i < items.length; i++) {
      items[i].size = '4';
      items[i].style.paddingLeft = '0px';
      items[i].style.paddingRight = '0px';
    }

  }, 100);
});