document.addEventListener("DOMContentLoaded", () => {
    const authToggles = Array.from(document.querySelectorAll("[data-auth-toggle]"));
    const authPanels = Array.from(document.querySelectorAll("[data-auth-panel]"));
    const authStorageKey = "pulseboard-auth-tab";

    if (authToggles.length && authPanels.length) {
        const setAuthTab = (tabName) => {
            authToggles.forEach((toggle) => {
                const isActive = toggle.dataset.authToggle === tabName;
                toggle.classList.toggle("active", isActive);
                toggle.setAttribute("aria-pressed", isActive ? "true" : "false");
            });

            authPanels.forEach((panel) => {
                panel.hidden = panel.dataset.authPanel !== tabName;
            });

            window.sessionStorage.setItem(authStorageKey, tabName);
        };

        const savedTab = window.sessionStorage.getItem(authStorageKey);
        setAuthTab(savedTab || "login");

        authToggles.forEach((toggle) => {
            toggle.addEventListener("click", () => {
                setAuthTab(toggle.dataset.authToggle);
            });
        });
    }

    document.querySelectorAll("[data-progress]").forEach((bar) => {
        requestAnimationFrame(() => {
            bar.style.width = `${bar.dataset.progress}%`;
        });
    });

    document.querySelectorAll("[data-autosubmit]").forEach((field) => {
        field.addEventListener("change", () => {
            if (field.form) {
                field.form.requestSubmit();
            }
        });
    });

    document.querySelectorAll("[data-flash]").forEach((flash, index) => {
        const hide = () => {
            flash.classList.add("is-hiding");
            window.setTimeout(() => flash.remove(), 220);
        };

        const closeButton = flash.querySelector("[data-flash-close]");
        if (closeButton) {
            closeButton.addEventListener("click", hide);
        }

        window.setTimeout(hide, 4500 + index * 300);
    });
});
