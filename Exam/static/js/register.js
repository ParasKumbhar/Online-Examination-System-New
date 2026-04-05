// register.js - Additional form handling
console.log('Register.js loaded');

document.addEventListener('DOMContentLoaded', function() {
    console.log('Register.js DOM ready');
    
    // Handle Enter key
    const handleEnterKey = function(e) {
        if (e.key !== 'Enter') return;
        e.preventDefault();
        
        const field = e.target;
        const tabindex = parseInt(field.getAttribute('tabindex')) || 0;
        
        const nextField = document.querySelector('[tabindex="' + (tabindex + 1) + '"]');
        if (nextField) {
            nextField.focus();
        } else if (tabindex === 5) {
            const submitBtn = document.querySelector('button[type="submit"]');
            if (submitBtn) submitBtn.click();
        }
    };
    
    // Add Enter handlers
    const fieldIds = ['id_username', 'id_email', 'id_password', 'id_confirm_password', 'id_picture'];
    fieldIds.forEach(function(id) {
        const field = document.getElementById(id);
        if (field) {
            field.addEventListener('keydown', handleEnterKey);
        }
    });
    
    console.log('Register.js initialization complete');
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
