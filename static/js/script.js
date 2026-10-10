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

// Registration checks and deleted-account confirmation
document.addEventListener("DOMContentLoaded", () => {
    // Username availability check
    const username = document.getElementById("username");
    const usernameStatus = document.getElementById("usernameStatus");
    let usernameTimer;

    if (username && usernameStatus) {
        username.addEventListener("input", function () {
            this.value = this.value.replace(/[^A-Za-z0-9_]/g, "");

            clearTimeout(usernameTimer);

            const value = this.value.trim();

            usernameStatus.textContent = "";
            usernameStatus.className = "form-text";

            if (!value) {
                return;
            }

            usernameTimer = setTimeout(() => {
                fetch(`/check-username?username=${encodeURIComponent(value)}`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error("Username check failed");
                        }

                        return response.json();
                    })
                    .then(data => {
                        // Ignore results for an outdated username.
                        if (username.value.trim() !== value) {
                            return;
                        }

                        usernameStatus.textContent = data.message;
                        usernameStatus.className = data.available
                            ? "form-text text-success"
                            : "form-text text-danger";
                    })
                    .catch(() => {
                        usernameStatus.textContent =
                            "Unable to check username.";
                        usernameStatus.className = "form-text text-danger";
                    });
            }, 300);
        });
    }

    // Email availability check
    const email = document.getElementById("email");
    const emailStatus = document.getElementById("emailStatus");
    let emailTimer;

    if (email && emailStatus) {
        email.addEventListener("input", function () {
            clearTimeout(emailTimer);

            const value = this.value.trim().toLowerCase();

            emailStatus.textContent = "";
            emailStatus.className = "form-text";

            if (!value) {
                return;
            }

            if (!email.checkValidity()) {
                emailStatus.textContent =
                    "Please enter a valid email address.";
                emailStatus.className = "form-text text-danger";
                return;
            }

            emailTimer = setTimeout(() => {
                fetch(`/check-email?email=${encodeURIComponent(value)}`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error("Email check failed");
                        }

                        return response.json();
                    })
                    .then(data => {
                        // Ignore results for an outdated email.
                        if (email.value.trim().toLowerCase() !== value) {
                            return;
                        }

                        emailStatus.textContent = data.message;
                        emailStatus.className = data.available
                            ? "form-text text-success"
                            : "form-text text-danger";
                    })
                    .catch(() => {
                        emailStatus.textContent =
                            "Unable to check email.";
                        emailStatus.className = "form-text text-danger";
                    });
            }, 300);
        });
    }

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