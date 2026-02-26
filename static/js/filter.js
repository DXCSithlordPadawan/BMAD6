/* static/js/filter.js — group filter for the template index page */
(function () {
  "use strict";
  var activeGroup = "__all__";

  function filterCards() {
    var cards = document.querySelectorAll("#template-grid .card");
    var visible = 0;
    cards.forEach(function (card) {
      if (activeGroup === "__all__") {
        card.style.display = "";
        visible++;
      } else {
        var raw = card.getAttribute("data-groups") || "";
        var groups = raw.split(",").map(function (g) {
          return g.trim();
        });
        if (groups.indexOf(activeGroup) !== -1) {
          card.style.display = "";
          visible++;
        } else {
          card.style.display = "none";
        }
      }
    });
    var noMsg = document.getElementById("no-match-msg");
    if (noMsg) noMsg.style.display = visible === 0 ? "" : "none";
  }

  document.querySelectorAll(".filter-chip").forEach(function (btn) {
    btn.addEventListener("click", function () {
      document.querySelectorAll(".filter-chip").forEach(function (b) {
        b.classList.remove("active");
      });
      btn.classList.add("active");
      activeGroup = btn.getAttribute("data-group");
      filterCards();
    });
  });
})();
