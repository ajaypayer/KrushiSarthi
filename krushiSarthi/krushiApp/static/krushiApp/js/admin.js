function validateAdminForm(formId) {
  const form = document.getElementById(formId);
  if (!form) return true;

  let valid = true;
  const requiredFields = form.querySelectorAll('[required]');

  requiredFields.forEach((field) => {
    if (!field.value.trim()) {
      valid = false;
      field.style.border = '1px solid red';
    } else {
      field.style.border = '';
    }
  });

  if (!valid) {
    alert('Please fill all required fields before submitting the admin form.');
  }

  return valid;
}

function validateLoginForm() {
  const username = document.getElementById('username');
  const password = document.getElementById('password');

  if (!username.value.trim() || !password.value.trim()) {
    alert('Please enter both username and password.');
    if (!username.value.trim()) username.style.border = '1px solid red';
    if (!password.value.trim()) password.style.border = '1px solid red';
    return false;
  }

  return true;
}
