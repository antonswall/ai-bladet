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

  if (document.querySelector(".lead")) {
    var progress = document.createElement("div");
    progress.className = "reading-progress";
    progress.setAttribute("aria-hidden", "true");
    document.body.appendChild(progress);
    var pending = false;
    function updateProgress() {
      var height = document.documentElement.scrollHeight - window.innerHeight;
      var ratio = height > 0 ? Math.min(1, Math.max(0, window.scrollY / height)) : 0;
      progress.style.transform = "scaleX(" + ratio + ")";
      pending = false;
    }
    function scheduleProgress() {
      if (pending) return;
      pending = true;
      requestAnimationFrame(updateProgress);
    }
    window.addEventListener("scroll", scheduleProgress, { passive: true });
    window.addEventListener("resize", scheduleProgress, { passive: true });
    document.addEventListener("click", scheduleProgress);
    updateProgress();
  }

  var atmosphere = document.querySelector(".masthead-atmosphere");
  var masthead = document.querySelector(".masthead");
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
  var finePointer = window.matchMedia("(hover: hover) and (pointer: fine)");
  if (atmosphere && masthead && !reduced.matches && finePointer.matches) {
    masthead.addEventListener("pointermove", function (event) {
      if (reduced.matches) return;
      var rect = masthead.getBoundingClientRect();
      atmosphere.style.setProperty("--field-x", ((event.clientX - rect.left) / rect.width - .5) * 16 + "px");
      atmosphere.style.setProperty("--field-y", ((event.clientY - rect.top) / rect.height - .5) * 10 + "px");
    }, { passive: true });
    masthead.addEventListener("pointerleave", function () {
      atmosphere.style.setProperty("--field-x", "0px");
      atmosphere.style.setProperty("--field-y", "0px");
    });
  }
})();

// Trasiga bilder tas bort (ersätter inline onerror, som CSP blockerar)
(function () {
  function drop(img) {
    var t = img.getAttribute("data-fail") === "parent" ? img.parentElement : img;
    if (t) t.remove();
  }
  document.addEventListener("error", function (e) {
    var el = e.target;
    if (el && el.tagName === "IMG" && el.hasAttribute("data-fail")) drop(el);
  }, true);
  document.querySelectorAll("img[data-fail]").forEach(function (img) {
    if (img.complete && img.naturalWidth === 0) drop(img);
  });
})();
