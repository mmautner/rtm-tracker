// Phase and status filters for agency pages. Without JavaScript every entry is shown.
(function () {
  var form = document.getElementById("filters");
  var list = document.getElementById("commitments");
  if (!form || !list) return;
  var items = Array.prototype.slice.call(list.querySelectorAll(".rt-item"));
  var phase = document.getElementById("f-phase");
  var status = document.getElementById("f-status");
  var count = document.getElementById("filter-count");

  function apply() {
    var p = phase.value, s = status.value, shown = 0;
    items.forEach(function (li) {
      var ok = (!p || li.dataset.phase === p) && (!s || li.dataset.status === s);
      li.hidden = !ok;
      if (ok) shown++;
    });
    count.textContent = "Showing " + shown + " of " + items.length + " recommendations";
    var q = new URLSearchParams();
    if (p) q.set("phase", p);
    if (s) q.set("status", s);
    var url = location.pathname + (q.toString() ? "?" + q : "") + location.hash;
    history.replaceState(null, "", url);
  }

  var params = new URLSearchParams(location.search);
  if (params.get("phase")) phase.value = params.get("phase");
  if (params.get("status")) status.value = params.get("status");
  phase.addEventListener("change", apply);
  status.addEventListener("change", apply);
  form.addEventListener("submit", function (e) { e.preventDefault(); });
  form.hidden = false;
  apply();

  // Open an entry linked by #id.
  if (location.hash) {
    var t = document.getElementById(location.hash.slice(1));
    if (t && t.querySelector("details")) t.querySelector("details").open = true;
  }
})();
