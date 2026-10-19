const themeKey = "expenseTrackerDarkMode";

function isLoggedIn() {
    return document.body.dataset.loggedIn === "true";
}

function applyTheme(enabled) {
    const loggedIn = isLoggedIn();
    const darkModeEnabled = loggedIn && enabled;

    document.body.classList.toggle("dark-mode", darkModeEnabled);

    if (loggedIn) {
        localStorage.setItem(themeKey, String(darkModeEnabled));
    } else {
        localStorage.removeItem(themeKey);
    }

    const toggle = document.getElementById("darkModeToggle");

    if (toggle) {
        toggle.checked = darkModeEnabled;
    }
}

// Theme setup
document.addEventListener("DOMContentLoaded", () => {
    const loggedIn = isLoggedIn();
    const toggle = document.getElementById("darkModeToggle");

    if (!loggedIn) {
        applyTheme(false);
    } else {
        const savedTheme = localStorage.getItem(themeKey) === "true";
        applyTheme(savedTheme);
    }

    if (toggle) {
        toggle.addEventListener("change", () => {
            applyTheme(toggle.checked);
        });
    }
});

// Password visibility toggles
document.addEventListener("DOMContentLoaded", () => {
    function setupPasswordToggle(inputId, buttonId) {
        const password = document.getElementById(inputId);
        const button = document.getElementById(buttonId);

        if (!password || !button) {
            return;
        }

        button.addEventListener("click", () => {
            const showing = password.type === "password";

            password.type = showing ? "text" : "password";
            button.textContent = showing ? "🙈" : "👁️";

            button.setAttribute(
                "aria-label",
                showing ? "Hide password" : "Show password"
            );

            button.setAttribute(
                "title",
                showing ? "Hide password" : "Show password"
            );
        });
    }

    setupPasswordToggle("password", "togglePassword");
    setupPasswordToggle("confirm_password", "toggleConfirmPassword");
});


 // Registration validation
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("registerForm");
    if (!form) return;

    const username = document.getElementById("username");
    const email = document.getElementById("email");
    const password = document.getElementById("password");
    const confirmPassword = document.getElementById("confirm_password");

    const usernameStatus = document.getElementById("usernameStatus");
    const emailStatus = document.getElementById("emailStatus");
    const passwordStatus = document.getElementById("passwordStatus");
    const confirmPasswordStatus =
        document.getElementById("confirmPasswordStatus");

    let usernameTimer;
    let emailTimer;
    let usernameRequest = 0;
    let emailRequest = 0;

    function showStatus(element, message, valid = false) {
        if (!element) return;

        element.textContent = message;
        element.className = valid
            ? "form-text text-success"
            : message
                ? "form-text text-danger"
                : "form-text";
    }

    function checkUsernameFormat() {
        const value = username.value.trim();

        if (!value) {
            showStatus(usernameStatus, "Username is required.");
            return false;
        }

        if (!/^[A-Za-z0-9_]{3,30}$/.test(value)) {
            showStatus(
                usernameStatus,
                "Use 3–30 characters: letters, numbers, and underscores only."
            );
            return false;
        }

        return true;
    }

    function checkEmailFormat() {
        const value = email.value.trim();

        if (!value) {
            showStatus(emailStatus, "Email address is required.");
            return false;
        }

        if (!email.validity.valid) {
            showStatus(emailStatus, "Please enter a valid email address.");
            return false;
        }

        return true;
    }

    function checkPassword() {
        if (!password.value) {
            showStatus(passwordStatus, "Password is required.");
            return false;
        }

        if (password.value.length < 8) {
            showStatus(
                passwordStatus,
                "Password must be at least 8 characters long."
            );
            return false;
        }

        if (password.value.length > 128) {
            showStatus(
                passwordStatus,
                "Password must not exceed 128 characters."
            );
            return false;
        }

        showStatus(passwordStatus, "Password length is valid.", true);
        return true;
    }

    function checkPasswordMatch() {
        if (!confirmPassword.value) {
            showStatus(
                confirmPasswordStatus,
                "Please confirm your password."
            );
            return false;
        }

        if (password.value !== confirmPassword.value) {
            showStatus(confirmPasswordStatus, "Passwords do not match.");
            return false;
        }

        showStatus(confirmPasswordStatus, "Passwords match.", true);
        return true;
    }

    async function checkAvailability(field, statusElement, endpoint, value, requestId) {
        try {
            const response = await fetch(
                `${endpoint}?${field}=${encodeURIComponent(value)}`
            );

            if (!response.ok) {
                throw new Error("Availability check failed.");
            }

            const data = await response.json();

            const requestIsCurrent =
                field === "username"
                    ? requestId === usernameRequest
                    : requestId === emailRequest;

            if (!requestIsCurrent) return false;

            showStatus(statusElement, data.message, data.available);
            return Boolean(data.available);
        } catch {
            const requestIsCurrent =
                field === "username"
                    ? requestId === usernameRequest
                    : requestId === emailRequest;

            if (requestIsCurrent) {
                showStatus(
                    statusElement,
                    `Unable to check ${field}. Please try again.`
                );
            }

            return false;
        }
    }

    username.addEventListener("input", () => {
        clearTimeout(usernameTimer);
        usernameRequest++;

        if (!checkUsernameFormat()) return;

        const value = username.value.trim();
        const requestId = usernameRequest;
        showStatus(usernameStatus, "Checking username…");

        usernameTimer = setTimeout(() => {
            checkAvailability(
                "username",
                usernameStatus,
                "/check-username",
                value,
                requestId
            );
        }, 300);
    });

    email.addEventListener("input", () => {
        clearTimeout(emailTimer);
        emailRequest++;

        if (!checkEmailFormat()) return;

        const value = email.value.trim().toLowerCase();
        const requestId = emailRequest;
        showStatus(emailStatus, "Checking email…");

        emailTimer = setTimeout(() => {
            checkAvailability(
                "email",
                emailStatus,
                "/check-email",
                value,
                requestId
            );
        }, 300);
    });

    password.addEventListener("input", () => {
        checkPassword();
        if (confirmPassword.value) checkPasswordMatch();
    });

    confirmPassword.addEventListener("input", checkPasswordMatch);

    // Validate all fields and wait for availability checks before submission.
form.addEventListener("submit", async (event) => {
    event.preventDefault();

    clearTimeout(usernameTimer);
    clearTimeout(emailTimer);

    const errors = [];

    const usernameValid = checkUsernameFormat();
    const emailValid = checkEmailFormat();
    const passwordValid = checkPassword();
    const confirmationValid = checkPasswordMatch();

    if (!usernameValid) {
        errors.push(usernameStatus.textContent);
    }

    if (!emailValid) {
        errors.push(emailStatus.textContent);
    }

    if (!passwordValid) {
        errors.push(passwordStatus.textContent);
    }

    if (!confirmationValid) {
        errors.push(confirmPasswordStatus.textContent);
    }

    let usernameAvailable = false;
    let emailAvailable = false;
    const checks = [];

    if (usernameValid) {
        const requestId = ++usernameRequest;
        showStatus(usernameStatus, "Checking username…");

        checks.push(
            checkAvailability(
                "username",
                usernameStatus,
                "/check-username",
                username.value.trim(),
                requestId
            ).then((available) => {
                usernameAvailable = available;
            })
        );
    } else {
        usernameRequest++;
    }

    if (emailValid) {
        const requestId = ++emailRequest;
        showStatus(emailStatus, "Checking email…");

        checks.push(
            checkAvailability(
                "email",
                emailStatus,
                "/check-email",
                email.value.trim().toLowerCase(),
                requestId
            ).then((available) => {
                emailAvailable = available;
            })
        );
    } else {
        emailRequest++;
    }

    await Promise.all(checks);

    if (usernameValid && !usernameAvailable) {
        errors.push(usernameStatus.textContent || "Username is unavailable.");
    }

    if (emailValid && !emailAvailable) {
        errors.push(emailStatus.textContent || "Email is unavailable.");
    }

    if (errors.length > 0) {
        let alertBox = form.parentElement.querySelector(
            "#registrationValidationAlert"
        );

        if (!alertBox) {
            alertBox = document.createElement("div");
            alertBox.id = "registrationValidationAlert";
            alertBox.className = "alert alert-danger";
            alertBox.setAttribute("role", "alert");
            form.parentElement.insertBefore(alertBox, form);
        }

        alertBox.replaceChildren();

        const heading = document.createElement("strong");
        heading.textContent = "Please fix the following errors:";
        alertBox.appendChild(heading);

        const list = document.createElement("ul");
        list.className = "mb-0 mt-2";

        [...new Set(errors.filter(Boolean))].forEach((message) => {
            const item = document.createElement("li");
            item.textContent = message;
            list.appendChild(item);
        });

        alertBox.appendChild(list);

        clearTimeout(alertBox.dismissTimer);

        alertBox.dismissTimer = setTimeout(() => {
            alertBox.remove();
        }, 10000);

        return;
    }

    form.submit();
    });
});

// Dismiss all Bootstrap alert boxes after 10 seconds.
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".alert").forEach((alert) => {
        setTimeout(() => {
            if (!alert.isConnected) return;

            if (window.bootstrap?.Alert) {
                window.bootstrap.Alert.getOrCreateInstance(alert).close();
            } else {
                alert.remove();
            }
        }, 10000);
    });
});


// Show or hide password fields
document.addEventListener("click", function (event) {
    const button = event.target.closest("[data-password-toggle]");

    if (!button) {
        return;
    }

    const inputId = button.dataset.passwordToggle;
    const input = document.getElementById(inputId);

    if (!input) {
        return;
    }

    if (input.type === "password") {
        input.type = "text";
        button.textContent = "🙈";
        button.setAttribute("aria-label", "Hide password");
    } else {
        input.type = "password";
        button.textContent = "👁️";
        button.setAttribute("aria-label", "Show password");
    }
});


// Expenses page: clear search, delete modal, and tooltips
document.addEventListener("DOMContentLoaded", () => {
    // Clear search while keeping other active filters.
    const clearSearchButton = document.querySelector("[data-clear-search]");

    if (clearSearchButton) {
        clearSearchButton.addEventListener("click", () => {
            const searchInput = document.querySelector('input[name="search"]');

            if (searchInput && searchInput.form) {
                searchInput.value = "";
                searchInput.form.submit();
            }
        });
    }

    // Set the correct expense URL when opening the delete modal.
    const deleteModal = document.getElementById("deleteModal");
    const deleteExpenseForm = document.getElementById("deleteExpenseForm");

    if (deleteModal && deleteExpenseForm) {
        deleteModal.addEventListener("show.bs.modal", (event) => {
            const button = event.relatedTarget;
            const deleteUrl = button?.getAttribute("data-delete-url");

            if (deleteUrl) {
                deleteExpenseForm.action = deleteUrl;
            }
        });
    }

    // Initialize tooltips only on pages that contain them.
    if (typeof bootstrap !== "undefined") {
        document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((element) => {
            bootstrap.Tooltip.getOrCreateInstance(element);
        });
    }
});


// Dashboard charts
document.addEventListener("DOMContentLoaded", () => {
    const categoryDataElement = document.getElementById("category-data");
    const timeDataElement = document.getElementById("time-data");
    const categoryCanvas = document.getElementById("categoryChart");
    const timeCanvas = document.getElementById("timeChart");

    // Do nothing when this isn't the dashboard page.
    if (
        !categoryDataElement ||
        !timeDataElement ||
        !categoryCanvas ||
        !timeCanvas
    ) {
        return;
    }

    // Chart.js is loaded by dashboard.html.
    if (typeof Chart === "undefined") {
        console.error("Chart.js failed to load.");
        return;
    }

    const categoryData = JSON.parse(categoryDataElement.textContent);
    const timeData = JSON.parse(timeDataElement.textContent);

    new Chart(categoryCanvas, {
        type: "bar",
        data: {
            labels: categoryData.map(item => item.category_name),
            datasets: [{
                label: "Spending",
                data: categoryData.map(item => item.total_amount)
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });

    new Chart(timeCanvas, {
        type: "line",
        data: {
            labels: timeData.map(item => item.date),
            datasets: [{
                label: "Spending",
                data: timeData.map(item => item.total_amount),
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
});