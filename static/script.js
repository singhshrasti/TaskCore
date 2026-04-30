document.addEventListener("DOMContentLoaded", () => {
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
