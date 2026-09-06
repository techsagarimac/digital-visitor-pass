(function () {
  const form = document.getElementById("registerForm");
  if (!form) return;

  const dateInput = document.getElementById("visit_date");
  if (dateInput && !dateInput.value) {
    const today = new Date().toISOString().slice(0, 10);
    dateInput.min = today;
    dateInput.value = today;
  }

  form.addEventListener("submit", function (event) {
    const entry = form.expected_entry.value;
    const exit = form.expected_exit.value;
    if (entry && exit && exit <= entry) {
      event.preventDefault();
      alert("Expected exit time must be after entry time.");
    }
  });
})();
