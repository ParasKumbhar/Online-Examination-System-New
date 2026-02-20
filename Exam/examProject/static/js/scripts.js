// scripts.js
console.log('JavaScript loaded successfully!');

// Global togglePassword function
function togglePassword(btn) {
    const container = btn.closest('.relative');
    if (!container) {
        console.log('No container found');
        return;
    }
    
    const input = container.querySelector('input');
    if (!input) {
        console.log('No input found');
        return;
    }
    
    if (input.type === 'password') {
        input.type = 'text';
        btn.innerHTML = '<i class="fa-solid fa-eye-slash"></i>';
        btn.setAttribute('aria-label', 'Hide password');
    } else {
        input.type = 'password';
        btn.innerHTML = '<i class="fa-solid fa-eye"></i>';
        btn.setAttribute('aria-label', 'Show password');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing forms...');
    
    // Attach click handlers to all password toggle buttons
    const toggleButtons = document.querySelectorAll('.showPasswordToggle');
    console.log('Found toggle buttons:', toggleButtons.length);
    
    toggleButtons.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Toggle clicked');
            togglePassword(this);
        });
    });
    
    // Handle Enter key navigation
    const handleEnterKey = function(e) {
        if (e.key !== 'Enter') return;
        
        const field = e.target;
        const tabindex = parseInt(field.getAttribute('tabindex')) || 0;
        
        // Check if this is a login form (only 2 input fields - username and password)
        const form = field.closest('form');
        const isLoginForm = form && 
            form.querySelectorAll('input[type="text"], input[type="email"], input[type="password"]').length === 2;
        
        // For login form, submit on Enter pressed on password field
        if (isLoginForm && field.type === 'password') {
            e.preventDefault();
            form.submit();
            return;
        }
        
        // For registration form, navigate to next field
        e.preventDefault();
        
        // Find next field
        const nextField = document.querySelector('[tabindex="' + (tabindex + 1) + '"]');
        if (nextField) {
            nextField.focus();
        } else if (tabindex === 5) {
            // Submit on last field (picture field in registration)
            const submitBtn = document.querySelector('button[type="submit"]');
            if (submitBtn) submitBtn.click();
        }
    };
    
    // Add Enter key handlers to form fields
    const fields = ['username', 'email', 'password', 'confirm_password', 'picture'];
    fields.forEach(function(fieldName) {
        const field = document.getElementById('id_' + fieldName) || document.querySelector('[name="' + fieldName + '"]');
        if (field) {
            field.addEventListener('keydown', handleEnterKey);
        }
    });
    
    // Username validation with debounce
    const usernameField = document.getElementById('id_username');
    const usernameFeedback = document.querySelector('.usernamevalidOut');
    let usernameTimeout = null;
    let isUsernameValid = false;
    
    if (usernameField && usernameFeedback) {
        usernameField.addEventListener('keyup', function(e) {
            const value = e.target.value;
            
            // Clear previous timeout
            if (usernameTimeout) {
                clearTimeout(usernameTimeout);
            }
            
            // Reset validation state
            usernameField.classList.remove('is-valid', 'is-invalid');
            usernameFeedback.classList.remove('valid-feedback', 'invalid-feedback');
            usernameFeedback.style.display = 'none';
            isUsernameValid = false;
            updateSubmitButton();
            
            if (value.length === 0) {
                return;
            }
            
            // Show checking message
            usernameFeedback.style.display = 'block';
            usernameFeedback.className = 'usernamevalidOut valid-feedback';
            usernameFeedback.textContent = 'Checking availability...';
            
            // Debounce the API call - wait 500ms after user stops typing
            usernameTimeout = setTimeout(function() {
                fetch('/student/username-validate', {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({username: value})
                })
                .then(function(res) { return res.json(); })
                .then(function(data) {
                    usernameFeedback.style.display = 'block';
                    
                    if (data.username_valid) {
                        // Username is available
                        usernameField.classList.remove('is-invalid');
                        usernameField.classList.add('is-valid');
                        usernameFeedback.className = 'usernamevalidOut valid-feedback text-green-600 text-sm mt-1';
                        usernameFeedback.textContent = '✓ Username is available';
                        isUsernameValid = true;
                    } else if (data.username_error) {
                        // Username has an error (exists or invalid format)
                        usernameField.classList.remove('is-valid');
                        usernameField.classList.add('is-invalid');
                        usernameFeedback.className = 'usernamevalidOut invalid-feedback text-red-600 text-sm mt-1';
                        usernameFeedback.textContent = '✗ ' + data.username_error;
                        isUsernameValid = false;
                    }
                    
                    updateSubmitButton();
                })
                .catch(function(err) {
                    console.log('Username check error:', err);
                    usernameFeedback.style.display = 'none';
                });
            }, 500);
        });
        
        // Also validate on blur when user leaves the field
        usernameField.addEventListener('blur', function(e) {
            const value = e.target.value;
            if (value.length > 0 && usernameTimeout) {
                clearTimeout(usernameTimeout);
                // Trigger immediate check
                usernameField.dispatchEvent(new Event('keyup'));
            }
        });
    }
    
    // Function to update submit button based on validation state
    function updateSubmitButton() {
        const submitBtn = document.querySelector('button[type="submit"]');
        if (submitBtn) {
            // If username field exists and has content but is not valid, disable submit
            if (usernameField && usernameField.value.length > 0 && !isUsernameValid) {
                submitBtn.disabled = true;
                submitBtn.classList.add('opacity-50', 'cursor-not-allowed');
            } else {
                submitBtn.disabled = false;
                submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            }
        }
    }
    
    console.log('Form initialization complete');
});

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
