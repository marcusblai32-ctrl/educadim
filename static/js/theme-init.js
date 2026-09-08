/**
 * Apply the saved EducDim theme before the page paints.
 * Keeping this tiny bootstrap separate from the main bundle prevents a
 * flash of the wrong theme without embedding JavaScript in templates.
 */
(function () {
  "use strict";

  var storageKey = "educdim-theme";
  var storedTheme = null;

  try {
    storedTheme = window.localStorage.getItem(storageKey);
  } catch (error) {
    storedTheme = null;
  }

  if (storedTheme !== "dark" && storedTheme !== "light") {
    storedTheme =
      window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
  }

  document.documentElement.setAttribute("data-theme", storedTheme);
})();