(function () {
  "use strict";

  function getCookie(name) {
    return document.cookie.split("; ").reduce(function (value, cookie) {
      var parts = cookie.split("=");
      return parts[0] === name ? decodeURIComponent(parts.slice(1).join("=")) : value;
    }, "");
  }

  function updateCard(card, data) {
    var previousStatus = card.dataset.todoStatus;
    card.classList.remove("todo-status-pending", "todo-status-in_progress", "todo-status-completed");
    card.classList.add("todo-status-" + data.status_key);
    card.dataset.todoStatus = data.status_key;
    var label = card.querySelector(".todo-status-label");
    if (label) label.textContent = data.status;
    updateStat(previousStatus, -1);
    updateStat(data.status_key, 1);
  }

  function updateStat(status, delta) {
    if (!status || status === "total") return;
    var stat = document.querySelector('[data-todo-stat="' + status + '"]');
    if (stat) stat.textContent = Math.max(0, Number(stat.textContent || 0) + delta);
  }

  function showFeedback(message, isError) {
    var feedback = document.querySelector("[data-todo-feedback]");
    if (!feedback) return;
    feedback.textContent = message;
    feedback.classList.toggle("todo-feedback-error", Boolean(isError));
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest(".todo-toggle");
    if (!button || button.dataset.loading === "true") return;

    var card = button.closest("[data-todo-card]");
    if (!card) return;
    card.classList.remove("todo-update-error");
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
        showFeedback("Statut de la tâche mis à jour.", false);
      })
      .catch(function () {
        card.classList.add("todo-update-error");
        showFeedback("Impossible de mettre à jour la tâche. Réessayez.", true);
      })
      .finally(function () {
        button.dataset.loading = "false";
        button.removeAttribute("aria-busy");
      });
  });
})();