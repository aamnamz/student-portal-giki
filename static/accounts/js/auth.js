document.addEventListener("DOMContentLoaded", function () {
    initPasswordToggles();
    initPasswordStrengthMeter();
    initNoDigitFields();
    initFormValidation();
});

/**
 * Eye / eye-slash toggle for any input paired with a
 * sibling span carrying data-password-toggle="<input id>".
 */
function initPasswordToggles() {
    document.querySelectorAll("[data-password-toggle]").forEach(function (toggleBtn) {
        toggleBtn.addEventListener("click", function () {
            const targetId = toggleBtn.getAttribute("data-password-toggle");
            const input = document.getElementById(targetId);
            if (!input) return;

            const isHidden = input.type === "password";
            input.type = isHidden ? "text" : "password";

            const icon = toggleBtn.querySelector("i");
            if (icon) {
                icon.classList.toggle("bi-eye", !isHidden);
                icon.classList.toggle("bi-eye-slash", isHidden);
            }
        });
    });
}

/**
 * Live password strength indicator on the signup form.
 */
function initPasswordStrengthMeter() {
    const pwInput = document.getElementById("id_password1");
    const fill = document.getElementById("pw-strength-fill");
    const label = document.getElementById("pw-strength-label");
    if (!pwInput || !fill || !label) return;

    const levels = [
        { min: 0, color: "#e3e8f0", text: "", width: "0%" },
        { min: 1, color: "#d33a4b", text: "Weak", width: "25%" },
        { min: 2, color: "#e0983c", text: "Fair", width: "50%" },
        { min: 3, color: "#2f5dc7", text: "Good", width: "75%" },
        { min: 4, color: "#1a8a5f", text: "Strong", width: "100%" },
    ];

    pwInput.addEventListener("input", function () {
        const value = pwInput.value;
        let score = 0;
        if (value.length >= 8) score++;
        if (/[A-Z]/.test(value) && /[a-z]/.test(value)) score++;
        if (/\d/.test(value)) score++;
        if (/[^A-Za-z0-9]/.test(value)) score++;

        const level = levels.slice().reverse().find((l) => score >= l.min) || levels[0];
        fill.style.width = level.width;
        fill.style.backgroundColor = level.color;
        label.textContent = value ? `Password strength: ${level.text}` : "";
    });
}

/**
 * Blocks digits/symbols from first & last name fields marked
 * data-no-digits="true", mirroring the server-side validator.
 */
function initNoDigitFields() {
    const ALLOWED_PATTERN = /^[A-Za-z\u00C0-\u024F' -]*$/;

    document.querySelectorAll('[data-no-digits="true"]').forEach(function (input) {
        input.addEventListener("keydown", function (event) {
            if (event.ctrlKey || event.metaKey || event.key.length > 1) return;
            if (!/^[A-Za-z\u00C0-\u024F' -]$/.test(event.key)) {
                event.preventDefault();
                flashInvalid(input);
            }
        });

        input.addEventListener("paste", function (event) {
            const pasted = (event.clipboardData || window.clipboardData).getData("text");
            if (!ALLOWED_PATTERN.test(pasted)) {
                event.preventDefault();
                flashInvalid(input);
            }
        });

        input.addEventListener("input", function () {
            if (!ALLOWED_PATTERN.test(input.value)) {
                input.value = input.value.replace(/[^A-Za-z\u00C0-\u024F' -]/g, "");
                flashInvalid(input);
            }
        });
    });

    function flashInvalid(input) {
        input.classList.add("is-invalid");
        setTimeout(() => input.classList.remove("is-invalid"), 600);
    }
}

/**
 * Highlights invalid fields immediately on a submit attempt,
 * for any form marked data-needs-validation.
 */
function initFormValidation() {
    document.querySelectorAll("form[data-needs-validation]").forEach(function (form) {
        form.addEventListener(
            "submit",
            function (event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add("was-validated");
            },
            false
        );
    });
}