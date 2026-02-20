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
        
        e.preventDefault();
        
        const field = e.target;
        const tabindex = parseInt(field.getAttribute('tabindex')) || 0;
        
        // Find next field
        const nextField = document.querySelector('[tabindex="' + (tabindex + 1) + '"]');
        if (nextField) {
            nextField.focus();
        } else if (tabindex === 5) {
            // Submit on last field
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
    
    // Username validation
    const usernameField = document.getElementById('id_username');
    const usernameFeedback = document.querySelector('.usernamevalidOut');
    if (usernameField && usernameFeedback) {
        usernameField.addEventListener('keyup', function(e) {
            const value = e.target.value;
            if (value.length > 0) {
                usernameFeedback.style.display = 'block';
                usernameFeedback.textContent = 'Checking username ' + value;
                
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
                    usernameFeedback.style.display = 'none';
                    if (data.username_error) {
                        usernameField.classList.add('is-invalid');
                    }
                })
                .catch(function(err) {
                    console.log('Username check error:', err);
                    usernameFeedback.style.display = 'none';
                });
            }
        });
    }
    
    // Email validation
    const emailField = document.getElementById('id_email');
    const emailFeedback = document.querySelector('.email-feedback');
    if (emailField && emailFeedback) {
        emailField.addEventListener('keyup', function(e) {
            const value = e.target.value;
            if (value.length > 0 && value.includes('@')) {
                fetch('/student/email-validate', {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({email: value})
                })
                .then(function(res) { return res.json(); })
                .then(function(data) {
                    if (data.email_error) {
                        emailField.classList.add('is-invalid');
                        emailFeedback.style.display = 'block';
                        emailFeedback.textContent = data.email_error;
                    }
                });
            }
        });
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
