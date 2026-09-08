(function () {
  "use strict";

  function getCookie(name) {
    return document.cookie.split("; ").reduce(function (value, cookie) {
      var parts = cookie.split("=");
      return parts[0] === name ? decodeURIComponent(parts.slice(1).join("=")) : value;
    }, "");
  }

  function updateCard(card, data) {
    card.classList.remove("todo-status-pending", "todo-status-in_progress", "todo-status-completed");
    card.classList.add("todo-status-" + data.status_key);
    var label = card.querySelector(".todo-status-label");
    if (label) label.textContent = data.status;
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest(".todo-toggle");
    if (!button || button.dataset.loading === "true") return;

    var card = button.closest("[data-todo-card]");
    button.dataset.loading = "true";
    button.setAttribute("aria-busy", "true");

    fetch(button.dataset.toggleUrl, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
        "X-Requested-With": "XMLHttpRequest",
        Accept: "application/json"
      },
      credentials: "same-origin"
    })
      .then(function (response) {
        if (!response.ok) throw new Error("Request failed");
        return response.json();
      })
      .then(function (data) {
        if (!data.success) throw new Error("Task update failed");
        updateCard(card, data);
      })
      .catch(function () {
        card.classList.add("todo-update-error");
      })
      .finally(function () {
        button.dataset.loading = "false";
        button.removeAttribute("aria-busy");
      });
  });
})();