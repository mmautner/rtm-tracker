// Google Analytics events for the tracker, sent to maxmautner.com's shared property. Every event is prefixed rtm_
// so it can be filtered from the blog's own events. Does nothing if the GA tag didn't load (blocked, offline).
(function () {
  var page = document.documentElement.getAttribute("data-page") || "overview";

  function track(name, params) {
    if (typeof gtag !== "function") return;
    var p = { page: page };
    for (var k in params || {}) p[k] = params[k];
    gtag("event", "rtm_" + name, p);
  }

  function entryOf(el) {
    var item = el.closest(".rt-item, .rt-ms");
    return item ? item.id : "";
  }

  document.addEventListener("click", function (ev) {
    var a = ev.target.closest("a");
    if (!a) return;
    var href = a.getAttribute("href") || "";

    if (href.indexOf("mailto:") === 0) {
      var subject = decodeURIComponent((href.split("subject=")[1] || "")).toLowerCase();
      track(subject.indexOf("agency suggestion") >= 0 ? "agency_suggestion_clicked" : "correction_email_clicked");
    } else if (/changelog\.xml$/.test(href)) {
      track("feed_clicked");
    } else if (/\/data\/[^/]+\.(csv|json)$/.test(href)) {
      track("download", { file: href.split("/").pop() });
    } else if (a.closest(".rt-sources, .rt-facts, .rt-cite") || a.classList.contains("rt-cite-link")) {
      var host = "";
      try { host = new URL(a.href).hostname; } catch (e) {}
      if (host && host !== location.hostname) track("source_clicked", { host: host, entry: entryOf(a) });
    }
  });

  // Disclosures: "Don't see your agency?", individual entries, milestone details
  document.addEventListener("toggle", function (ev) {
    var d = ev.target;
    if (!d.open) return;
    if (d.id === "other-agencies") track("other_agencies_opened");
    else if (d.closest(".rt-item")) track("entry_opened", { entry: entryOf(d) });
    else if (d.closest(".rt-ms")) track("milestone_opened", { milestone: entryOf(d) });
  }, true);

  // Filters on agency pages
  document.addEventListener("change", function (ev) {
    var t = ev.target;
    if (t.id === "f-phase" || t.id === "f-status" || t.id === "f-kind") track("filter_changed", { filter: t.name, value: t.value || "all" });
  });
})();
