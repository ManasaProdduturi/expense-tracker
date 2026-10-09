const themeKey = "expenseTrackerDarkMode";

function applyTheme(enabled) {
    document.body.classList.toggle("dark-mode", enabled);
    localStorage.setItem(themeKey, enabled ? "true" : "false");

    const toggle = document.getElementById("darkModeToggle");
    if (toggle) toggle.checked = enabled;
}

document.addEventListener("DOMContentLoaded", () => {
    const enabled = localStorage.getItem(themeKey) === "true";
    document.body.classList.toggle("dark-mode", enabled);

    const toggle = document.getElementById("darkModeToggle");
    if (toggle) {
        toggle.checked = enabled;
        toggle.addEventListener("change", () => applyTheme(toggle.checked));
    }
});