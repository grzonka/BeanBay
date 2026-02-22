/**
 * tags.js — Flavor tag input behavior for the feedback panel.
 *
 * Handles:
 * - Adding tags via Enter or comma key in the text input
 * - Removing tags via the ✕ chip button
 * - Max 10 tags enforcement
 * - Updating hidden input with comma-separated tag values
 * - Form submit: strips name from untouched flavor sliders so they submit null
 */

(function () {
  "use strict";

  var MAX_TAGS = 10;
  var tags = [];

  function updateHidden() {
    var hidden = document.getElementById("flavor-tags-hidden");
    if (hidden) {
      hidden.value = tags.join(",");
    }
  }

  function renderTags() {
    var list = document.getElementById("tag-list");
    var input = document.getElementById("tag-input");
    if (!list) return;

    list.innerHTML = "";
    tags.forEach(function (tag, index) {
      var chip = document.createElement("span");
      chip.className = "tag-chip";
      chip.textContent = tag;

      var remove = document.createElement("button");
      remove.type = "button";
      remove.className = "tag-chip-remove";
      remove.setAttribute("aria-label", "Remove " + tag);
      remove.textContent = "✕";
      remove.addEventListener("click", function () {
        tags.splice(index, 1);
        renderTags();
        updateHidden();
        // Re-enable input if under limit
        if (input) input.disabled = false;
      });

      chip.appendChild(remove);
      list.appendChild(chip);
    });

    // Disable input when at max
    if (input) {
      input.disabled = tags.length >= MAX_TAGS;
      if (input.disabled) {
        input.placeholder = "Max " + MAX_TAGS + " tags reached";
      } else {
        input.placeholder = "Type a flavor (e.g. chocolate, citrus)...";
      }
    }

    updateHidden();
  }

  function addTag(value) {
    var trimmed = value.trim().replace(/,+$/, "").trim();
    if (!trimmed) return false;
    if (tags.length >= MAX_TAGS) return false;
    if (tags.indexOf(trimmed) !== -1) return false; // no duplicates
    tags.push(trimmed);
    renderTags();
    return true;
  }

  function initTagInput() {
    var input = document.getElementById("tag-input");
    if (!input) return;

    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === ",") {
        e.preventDefault();
        if (addTag(input.value)) {
          input.value = "";
        } else {
          // Clear comma/trailing whitespace
          input.value = input.value.replace(/,+$/, "").trim();
        }
      }
    });

    // Also support adding on blur (user taps away after typing a tag)
    input.addEventListener("blur", function () {
      if (input.value.trim()) {
        if (addTag(input.value)) {
          input.value = "";
        }
      }
    });
  }

  function initFlavorSliders() {
    // On form submit, remove name from untouched sliders so they don't submit
    document.addEventListener("submit", function (e) {
      var form = e.target;
      var sliders = form.querySelectorAll(".flavor-slider");
      sliders.forEach(function (slider) {
        if (slider.dataset.touched !== "true") {
          slider.removeAttribute("name");
        }
      });
    });
  }

  function init() {
    initTagInput();
    initFlavorSliders();
  }

  // Run after DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
