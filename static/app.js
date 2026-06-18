// AI-Bladet — minimal progressive enhancement
// Inline "Läs mer" / "Läs mindre" toggle for story bodies on the front page.
(function () {
  "use strict";

  document.addEventListener("click", function (e) {
    var btn = e.target.closest(".story-more");
    if (!btn) return;

    var id = btn.getAttribute("aria-controls");
    var wrap = id && document.getElementById(id);
    if (!wrap) return;

    var expanded = btn.getAttribute("aria-expanded") === "true";
    expanded = !expanded;

    btn.setAttribute("aria-expanded", String(expanded));
    wrap.hidden = !expanded;

    var label = btn.querySelector(".story-more-label");
    var arrow = btn.querySelector(".story-more-arrow");
    if (label) label.textContent = expanded ? "Läs mindre" : "Läs mer";
    if (arrow) arrow.textContent = expanded ? "↑" : "→";

    btn.closest(".story-card").classList.toggle("is-expanded", expanded);
  });
})();
