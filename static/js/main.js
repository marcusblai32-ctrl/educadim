/*
 * EducDim — main.js
 * Complete JavaScript for navigation, dropdowns, animations
 * Version 4.0 - Final
 */

/* ============================================
 * DARK / LIGHT THEME TOGGLE
 * Persists via localStorage, syncs across tabs.
 * ============================================ */
(function () {
  "use strict";

  var STORAGE_KEY = "educdim-theme";
  var root = document.documentElement;

  function currentTheme() {
    return root.getAttribute("data-theme") === "dark" ? "dark" : "light";
  }

  function syncButtons(theme) {
    var buttons = document.querySelectorAll("#themeToggle, .theme-toggle");
    buttons.forEach(function (btn) {
      var icon = btn.querySelector("i");
      if (icon) {
        icon.className = theme === "dark" ? "fas fa-sun" : "fas fa-moon";
      }
      btn.setAttribute("aria-pressed", String(theme === "dark"));
    });
  }

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (e) {}
    syncButtons(theme);
  }

  function toggleTheme() {
    applyTheme(currentTheme() === "dark" ? "light" : "dark");
  }

  document.addEventListener("DOMContentLoaded", function () {
    syncButtons(currentTheme());
    document.querySelectorAll("#themeToggle, .theme-toggle").forEach(function (btn) {
      btn.addEventListener("click", toggleTheme);
    });
  });

  // Keep multiple open tabs in sync.
  window.addEventListener("storage", function (e) {
    if (e.key === STORAGE_KEY && (e.newValue === "dark" || e.newValue === "light")) {
      root.setAttribute("data-theme", e.newValue);
      syncButtons(e.newValue);
    }
  });
})();

(function () {
  "use strict";

  function initEducDim() {
    var menuToggle = document.getElementById("menuToggle");
    var mainNav = document.getElementById("mainNav");
    var loadingOverlay = document.getElementById("loadingOverlay");

    var dropdownButtons = document.querySelectorAll(
      "#chatDropdownBtn, #userDropdownBtn, .nav-dropdown-btn, .dropbtn"
    );
    var dropdowns = document.querySelectorAll(".nav-dropdown, .user-dropdown");
    var closeAlerts = document.querySelectorAll(".close-alert");
    var revealItems = document.querySelectorAll(".animate-on-scroll, .reveal, .reveal-two, .reveal-three");
    var statNumbers = document.querySelectorAll(".stat-number");

    function isMobile() {
      return window.matchMedia("(max-width: 768px)").matches;
    }

    function setExpanded(button, expanded) {
      if (button) button.setAttribute("aria-expanded", String(expanded));
    }

    function setMenuIcon(open) {
      if (!menuToggle) return;
      var icon = menuToggle.querySelector("i, svg");
      if (icon) {
        if (icon.classList.contains("fa-bars") || icon.classList.contains("fa-times")) {
          icon.className = open ? "fas fa-times" : "fas fa-bars";
        }
      }
      menuToggle.setAttribute("aria-expanded", String(open));
      menuToggle.setAttribute("aria-label", open ? "Fermer le menu" : "Ouvrir le menu");
    }

    function closeDropdown(dropdown) {
      dropdown.classList.remove("open");
      setExpanded(dropdown.querySelector(".nav-dropdown-btn, .dropbtn"), false);
    }

    function closeAllDropdowns(except) {
      dropdowns.forEach(function (dropdown) {
        if (dropdown !== except) closeDropdown(dropdown);
      });
    }

    function closeMenu() {
      if (!mainNav) return;
      mainNav.classList.remove("active");
      setMenuIcon(false);
      closeAllDropdowns();
    }

    function toggleMenu(event) {
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      if (!mainNav || !isMobile()) return;
      var open = !mainNav.classList.contains("active");
      if (open) {
        closeAllDropdowns();
        mainNav.classList.add("active");
        setMenuIcon(true);
      } else {
        closeMenu();
      }
    }

    // ============================================
    // MOBILE MENU TOGGLE
    // ============================================
    if (menuToggle && mainNav) {
      menuToggle.addEventListener("click", toggleMenu);
      setMenuIcon(mainNav.classList.contains("active"));
    }

    // ============================================
    // DROPDOWNS - Délégation d'événements
    // ============================================
    dropdownButtons.forEach(function (button) {
      button.setAttribute("aria-expanded", "false");
      button.addEventListener("click", function (event) {
        event.preventDefault();
        event.stopPropagation();

        var dropdown = button.closest(".nav-dropdown, .user-dropdown");
        if (!dropdown) return;

        var open = !dropdown.classList.contains("open");
        closeAllDropdowns(dropdown);
        dropdown.classList.toggle("open", open);
        setExpanded(button, open);
      });
    });

    // ============================================
    // CLOSE ON OUTSIDE CLICK
    // ============================================
    document.addEventListener("click", function (event) {
      var target = event.target;
      if (!(target instanceof Element)) return;

      if (!target.closest(".nav-dropdown, .user-dropdown")) {
        closeAllDropdowns();
      }

      if (
        isMobile() &&
        !target.closest("#mainNav") &&
        !target.closest("#menuToggle")
      ) {
        closeMenu();
      }
    });

    // ============================================
    // CLOSE ON ESCAPE KEY
    // ============================================
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        closeAllDropdowns();
        closeMenu();
      }
    });

    // ============================================
    // CLOSE ALERTS
    // ============================================
    closeAlerts.forEach(function (button) {
      button.addEventListener("click", function () {
        var alert = button.closest(".alert");
        if (alert) {
          alert.style.transition = "all 0.3s ease";
          alert.style.opacity = "0";
          alert.style.transform = "translateX(20px)";
          setTimeout(function () {
            if (alert.parentNode) alert.remove();
          }, 300);
        }
      });
    });

    // Auto-dismiss alerts after 5 seconds
    document.querySelectorAll(".alert:not(.alert-persistent)").forEach(function (alert) {
      setTimeout(function () {
        if (alert && alert.parentNode) {
          alert.style.transition = "all 0.3s ease";
          alert.style.opacity = "0";
          alert.style.transform = "translateX(20px)";
          setTimeout(function () {
            if (alert.parentNode) alert.remove();
          }, 300);
        }
      }, 5000);
    });

    // ============================================
    // CLOSE MENU ON NAV LINK CLICK (MOBILE)
    // ============================================
    document.querySelectorAll("#mainNav a, .footer-container nav a").forEach(function (link) {
      link.addEventListener("click", function () {
        if (isMobile()) closeMenu();
      });
    });

    // ============================================
    // SMOOTH SCROLL FOR ANCHOR LINKS
    // ============================================
    document.querySelectorAll('a[href^="#"]').forEach(function (link) {
      link.addEventListener("click", function (event) {
        var href = link.getAttribute("href");
        if (!href || href === "#" || href.length < 2) return;
        var target = document.querySelector(href);
        if (!target) return;
        event.preventDefault();
        var headerOffset = 80;
        var elementPosition = target.getBoundingClientRect().top;
        var offsetPosition = elementPosition + window.pageYOffset - headerOffset;
        window.scrollTo({
          top: offsetPosition,
          behavior: "smooth"
        });
        if (isMobile()) closeMenu();
      });
    });

    // ============================================
    // SCROLL REVEAL ANIMATIONS
    // ============================================
    if ("IntersectionObserver" in window) {
      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible");
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: 0.12, rootMargin: "0px 0px -30px 0px" });
      revealItems.forEach(function (item) { observer.observe(item); });
    } else {
      revealItems.forEach(function (item) { item.classList.add("visible"); });
    }

    // ============================================
    // STATS COUNTER ANIMATION
    // ============================================
    if (statNumbers.length) {
      var statTargets = [];

      statNumbers.forEach(function (stat) {
        var target = parseInt(stat.getAttribute("data-target"));
        if (!target) {
          var textContent = stat.textContent.replace(/[^0-9]/g, "");
          target = parseInt(textContent);
          if (isNaN(target) || target === 0) return;
          stat.setAttribute("data-target", target);
        }

        statTargets.push({
          element: stat,
          target: target,
          suffix: stat.textContent.replace(/[0-9]/g, ""),
          animated: false
        });
      });

      function animateCounter(data) {
        if (data.animated) return;
        data.animated = true;

        var duration = 2000;
        var startTime = null;
        var target = data.target;
        var element = data.element;
        var suffix = data.suffix;

        function updateCounter(timestamp) {
          if (!startTime) startTime = timestamp;
          var progress = Math.min((timestamp - startTime) / duration, 1);
          var eased = 1 - Math.pow(1 - progress, 3);
          var current = Math.floor(eased * target);
          element.textContent = current + suffix;
          if (progress < 1) {
            requestAnimationFrame(updateCounter);
          } else {
            element.textContent = target + suffix;
          }
        }

        requestAnimationFrame(updateCounter);
      }

      if ("IntersectionObserver" in window) {
        var statsObserver = new IntersectionObserver(function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              var index = statTargets.findIndex(function (item) {
                return item.element === entry.target;
              });
              if (index !== -1 && !statTargets[index].animated) {
                animateCounter(statTargets[index]);
              }
              statsObserver.unobserve(entry.target);
            }
          });
        }, { threshold: 0.5 });

        statNumbers.forEach(function (stat) {
          statsObserver.observe(stat);
        });
      } else {
        statTargets.forEach(function (data) {
          animateCounter(data);
        });
      }
    }

    // ============================================
    // FEATURE CARD HOVER EFFECTS
    // ============================================
    var featureCards = document.querySelectorAll(".feature-card");
    featureCards.forEach(function (card) {
      card.addEventListener("mouseenter", function () {
        var icon = this.querySelector(".feature-icon, .feature-icon-wrapper");
        if (icon) {
          icon.style.transition = "transform 0.3s ease";
          icon.style.transform = "scale(1.1) rotate(5deg)";
        }
      });
      card.addEventListener("mouseleave", function () {
        var icon = this.querySelector(".feature-icon, .feature-icon-wrapper");
        if (icon) {
          icon.style.transform = "scale(1) rotate(0deg)";
        }
      });
    });

    // ============================================
    // TESTIMONIAL CARD HOVER
    // ============================================
    var testimonialCards = document.querySelectorAll(".testimonial-card");
    testimonialCards.forEach(function (card) {
      card.addEventListener("mouseenter", function () {
        this.style.transition = "transform 0.3s ease, box-shadow 0.3s ease";
        this.style.transform = "translateY(-6px)";
      });
      card.addEventListener("mouseleave", function () {
        this.style.transform = "translateY(0)";
      });
    });

    // ============================================
    // HEADER SCROLL EFFECT
    // ============================================
    var header = document.querySelector(".main-header");
    if (header) {
      window.addEventListener("scroll", function () {
        if (window.scrollY > 50) {
          header.classList.add("scrolled");
        } else {
          header.classList.remove("scrolled");
        }
      }, { passive: true });
    }

    // ============================================
    // LOADING OVERLAY
    // ============================================
    if (loadingOverlay) {
      loadingOverlay.classList.add("active");
      window.setTimeout(function () {
        loadingOverlay.classList.remove("active");
        loadingOverlay.style.opacity = "0";
        setTimeout(function () {
          loadingOverlay.style.display = "none";
        }, 400);
      }, 350);
    }

    // ============================================
    // SWIPER CAROUSEL (if available)
    // ============================================
    if (typeof Swiper !== "undefined") {
      var swiperEl = document.querySelector(".banner-swiper, .swiper-container");
      if (swiperEl) {
        new Swiper(swiperEl, {
          loop: true,
          autoplay: {
            delay: 5000,
            disableOnInteraction: false
          },
          pagination: {
            el: ".swiper-pagination",
            clickable: true
          },
          navigation: {
            nextEl: ".swiper-button-next",
            prevEl: ".swiper-button-prev"
          },
          effect: "slide",
          speed: 600
        });
      }
    }

    // ============================================
    // LAZY LOAD IMAGES
    // ============================================
    if ("IntersectionObserver" in window) {
      var lazyImages = document.querySelectorAll(".hero-photo-frame img, .about-photo-wrap img, .testimonial-person img");
      var imageObserver = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            var img = entry.target;
            if (img.dataset.src) {
              img.src = img.dataset.src;
              img.removeAttribute("data-src");
            }
            img.classList.add("loaded");
            imageObserver.unobserve(img);
          }
        });
      }, { rootMargin: "50px" });

      lazyImages.forEach(function (img) {
        imageObserver.observe(img);
      });
    }

    // ============================================
    // PARALLAX EFFECT ON HERO
    // ============================================
    var heroOrbits = document.querySelectorAll(".hero-orbit");
    if (heroOrbits.length) {
      window.addEventListener("scroll", function () {
        var scrolled = window.pageYOffset;
        heroOrbits.forEach(function (orbit, index) {
          var speed = index === 0 ? 0.15 : 0.25;
          var translateY = scrolled * speed * 0.05;
          var translateX = scrolled * speed * 0.02;
          orbit.style.transform = "translate(" + translateX + "px, " + translateY + "px)";
        });
      }, { passive: true });
    }

    // ============================================
    // RESIZE HANDLER
    // ============================================
    var resizeTimer;
    window.addEventListener("resize", function () {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(function () {
        if (!isMobile()) {
          closeMenu();
        } else {
          closeAllDropdowns();
        }
      }, 250);
    });

    console.log("EducDim initialized successfully");
  }

  // ============================================
  // INITIALIZATION
  // ============================================
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initEducDim);
  } else {
    initEducDim();
  }

  // Re-initialize on dynamic navigation
  if (typeof Turbolinks !== "undefined") {
    document.addEventListener("turbolinks:load", function () {
      setTimeout(initEducDim, 100);
    });
  }

  if (typeof htmx !== "undefined") {
    document.addEventListener("htmx:afterSwap", function () {
      setTimeout(initEducDim, 100);
    });
  }

  // Expose for manual re-init
  window.EducDim = {
    init: initEducDim,
    version: "4.0.0"
  };
})();

/* ============================================
   GLOBAL FILE INPUT HANDLER - SAN KLAS
   ============================================ */

(function() {
    'use strict';

    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        initFileInputs();
    });

    // Dynamic content
    document.addEventListener('htmx:afterSwap', function() {
        initFileInputs();
    });
    
    document.addEventListener('turbo:load', function() {
        initFileInputs();
    });

    // MutationObserver
    const observer = new MutationObserver(function(mutations) {
        let needsInit = false;
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length > 0) {
                needsInit = true;
            }
        });
        if (needsInit) {
            initFileInputs();
        }
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    /**
     * Initialize all file inputs - Selectè: input[type="file"]
     */
    function initFileInputs() {
        const fileInputs = document.querySelectorAll('input[type="file"]:not([data-file-initialized])');
        
        fileInputs.forEach(function(input) {
            // Mark as initialized
            input.dataset.fileInitialized = 'true';
            
            // Get placeholder from attribute or default
            const placeholder = input.getAttribute('data-placeholder') || 
                               input.getAttribute('placeholder') || 
                               'Choisir un fichier';
            
            // Set default text
            input.setAttribute('data-placeholder-text', placeholder);
            
            // Restore state if file already selected
            if (input.value) {
                const fileName = input.value.split('\\').pop();
                input.dataset.hasFile = 'true';
                input.dataset.fileName = fileName;
                input.setAttribute('data-file-name', fileName);
            }
            
            // Event listeners
            input.addEventListener('change', function(e) {
                handleFileChange(e);
            });
            
            input.addEventListener('click', function(e) {
                // Allow re-selection
                this.value = '';
            });
        });
    }

    /**
     * Handle file change
     */
    function handleFileChange(event) {
        const input = event.target;
        const file = input.files && input.files[0];

        // Remove error state
        input.removeAttribute('data-error');

        if (file) {
            // Validate file size (20MB max)
            const maxSize = 20 * 1024 * 1024;
            if (file.size > maxSize) {
                input.setAttribute('data-error', 'true');
                showNotification('File too large. Maximum 20MB allowed.', 'error');
                input.value = '';
                input.removeAttribute('data-has-file');
                input.removeAttribute('data-file-name');
                return;
            }

            // Validate file type
            const accept = input.getAttribute('accept');
            if (accept && accept !== '*/*') {
                const acceptedTypes = accept.split(',').map(t => t.trim());
                const fileType = file.type;
                const fileExt = '.' + file.name.split('.').pop().toLowerCase();
                
                let isValid = false;
                acceptedTypes.forEach(function(type) {
                    if (type === fileType || type === fileExt) {
                        isValid = true;
                    }
                    if (type.endsWith('/*')) {
                        const baseType = type.replace('/*', '');
                        if (fileType.startsWith(baseType)) {
                            isValid = true;
                        }
                    }
                });
                
                if (!isValid) {
                    input.setAttribute('data-error', 'true');
                    showNotification('Invalid file type. Please select a valid file.', 'error');
                    input.value = '';
                    input.removeAttribute('data-has-file');
                    input.removeAttribute('data-file-name');
                    return;
                }
            }

            // Success
            input.removeAttribute('data-error');
            input.dataset.hasFile = 'true';
            input.dataset.fileName = file.name;
            input.setAttribute('data-file-name', file.name);

            // Dispatch event
            input.dispatchEvent(new CustomEvent('fileSelected', {
                detail: { file: file, input: input }
            }));

            // Try to show preview if preview container exists
            showPreviewForInput(input, file);

        } else {
            // No file selected
            input.removeAttribute('data-has-file');
            input.removeAttribute('data-file-name');
            input.removeAttribute('data-error');
            
            // Remove preview
            const preview = findPreviewContainer(input);
            if (preview) {
                preview.innerHTML = '';
                preview.style.display = 'none';
            }
        }
    }

    /**
     * Find preview container for an input
     */
    function findPreviewContainer(input) {
        // Check if preview exists next to input
        let sibling = input.nextElementSibling;
        while (sibling) {
            if (sibling.tagName === 'DIV' && sibling.classList.contains('file-preview')) {
                return sibling;
            }
            if (sibling.tagName === 'DIV' && sibling.querySelector('.file-preview')) {
                return sibling.querySelector('.file-preview');
            }
            sibling = sibling.nextElementSibling;
        }
        return null;
    }

    /**
     * Show preview for file
     */
    function showPreviewForInput(input, file) {
        const preview = findPreviewContainer(input);
        if (!preview) return;

        preview.style.display = 'block';
        preview.innerHTML = '';

        const fileType = file.type;
        const fileSize = formatFileSize(file.size);

        if (fileType.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = document.createElement('img');
                img.src = e.target.result;
                img.alt = file.name;
                img.style.maxHeight = '200px';
                img.style.maxWidth = '100%';
                img.style.borderRadius = '6px';
                preview.appendChild(img);
                addFileInfo(preview, file.name, fileSize, input);
            };
            reader.readAsDataURL(file);
            
        } else if (fileType.startsWith('audio/')) {
            const audio = document.createElement('audio');
            audio.controls = true;
            audio.style.maxWidth = '100%';
            audio.style.borderRadius = '6px';
            const source = document.createElement('source');
            source.src = URL.createObjectURL(file);
            source.type = fileType;
            audio.appendChild(source);
            preview.appendChild(audio);
            addFileInfo(preview, file.name, fileSize, input);
            
        } else if (fileType.startsWith('video/')) {
            const video = document.createElement('video');
            video.controls = true;
            video.style.maxWidth = '100%';
            video.style.borderRadius = '6px';
            const source = document.createElement('source');
            source.src = URL.createObjectURL(file);
            source.type = fileType;
            video.appendChild(source);
            preview.appendChild(video);
            addFileInfo(preview, file.name, fileSize, input);
            
        } else {
            // Other files
            const link = document.createElement('a');
            link.href = URL.createObjectURL(file);
            link.target = '_blank';
            link.style.cssText = `
                display: inline-flex;
                align-items: center;
                gap: 8px;
                padding: 8px 12px;
                background: var(--bs-primary, #007bff);
                color: white;
                border-radius: 4px;
                text-decoration: none;
                font-weight: 500;
            `;
            link.innerHTML = '📄 ' + escapeHtml(file.name) + ' <span style="font-size:13px;opacity:0.8;">(' + fileSize + ')</span>';
            preview.appendChild(link);
            addFileInfo(preview, file.name, fileSize, input);
        }
    }

    /**
     * Add file info with remove button
     */
    function addFileInfo(container, fileName, fileSize, input) {
        const info = document.createElement('div');
        info.style.cssText = `
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
            padding: 8px 12px;
            background: var(--bs-light, #f8f9fa);
            border-radius: 4px;
            border: 1px solid var(--bs-border-color, #e9ecef);
            margin-top: 10px;
        `;
        info.innerHTML = `
            <span style="font-weight:500;">${escapeHtml(fileName)}</span>
            <span style="color:var(--bs-secondary-color, #6c757d);font-size:13px;">${fileSize}</span>
            <button type="button" style="
                background: none;
                border: none;
                color: var(--bs-danger, #dc3545);
                cursor: pointer;
                font-size: 18px;
                padding: 0 5px;
                line-height: 1;
                margin-left: auto;
            " title="Retirer le fichier">✕</button>
        `;
        container.appendChild(info);

        // Remove button handler
        const removeBtn = info.querySelector('button');
        removeBtn.addEventListener('click', function(e) {
            e.preventDefault();
            input.value = '';
            input.dispatchEvent(new Event('change'));
        });
    }

    /**
     * Format file size
     */
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    /**
     * Escape HTML
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Show notification
     */
    function showNotification(message, type) {
        let notification = document.getElementById('global-file-notification');
        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'global-file-notification';
            notification.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                padding: 15px 25px;
                border-radius: 8px;
                color: white;
                font-size: 14px;
                z-index: 9999;
                max-width: 400px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                transform: translateY(100px);
                opacity: 0;
                transition: all 0.3s ease;
                pointer-events: none;
            `;
            document.body.appendChild(notification);
        }

        const colors = {
            error: '#dc3545',
            success: '#28a745',
            warning: '#ffc107',
            info: '#17a2b8'
        };
        notification.style.background = colors[type] || colors.info;
        notification.textContent = message;

        clearTimeout(notification._hideTimeout);
        setTimeout(function() {
            notification.style.transform = 'translateY(0)';
            notification.style.opacity = '1';
        }, 10);

        notification._hideTimeout = setTimeout(function() {
            notification.style.transform = 'translateY(100px)';
            notification.style.opacity = '0';
        }, 5000);
    }

    // Expose for global use
    window.GlobalFileHandler = {
        init: initFileInputs,
        showNotification: showNotification,
        formatFileSize: formatFileSize
    };

})();
