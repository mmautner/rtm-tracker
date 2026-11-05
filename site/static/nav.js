// Agency menu in the tracker nav. It is a <details> element, so it opens and closes without this
// script; this adds closing on an outside click or Escape, and opens "Don't see your agency?" on the
// overview when linked to it.
(function () {
  var menu = document.getElementById("agency-menu");
  if (menu) {
    document.addEventListener("click", function (e) {
      if (menu.open && !menu.contains(e.target)) menu.open = false;
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && menu.open) { menu.open = false; menu.querySelector("summary").focus(); }
    });
  }
  function openOther() {
    if (location.hash !== "#other-agencies") return;
    var d = document.getElementById("other-agencies");
    if (d) { d.open = true; d.scrollIntoView(); }
    if (menu) menu.open = false;
  }
  window.addEventListener("hashchange", openOther);
  openOther();
})();
