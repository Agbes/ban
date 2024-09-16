const tabs = document.querySelectorAll('.auth-tab');
const forms = document.querySelectorAll('.auth-form');

tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        const target = tab.getAttribute('data-tab');
        
        tabs.forEach(t => t.classList.remove('active'));
        forms.forEach(f => f.classList.remove('active'));
        
        tab.classList.add('active');
        document.getElementById(`${target}-form`).classList.add('active');

        // Clear all error and success messages when switching tabs
        document.querySelectorAll('.error, .success').forEach(el => el.textContent = '');
    });
});

const loginForm = document.getElementById('login-form');

loginForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    
    // Reset error messages
    document.getElementById('login-username-error').textContent = '';
    document.getElementById('login-password-error').textContent = '';
    document.getElementById('login-success').textContent = '';

    // Simple validation
    let isValid = true;

    if (!username) {
        document.getElementById('login-username-error').textContent = 'Le nom utilisateur est requise';
        isValid = false;
    }

    if (!password) {
        document.getElementById('login-password-error').textContent = 'Le mot de passe est requis';
        isValid = false;
    }

    if (isValid) {
        // Simulate login (replace with actual login logic)
        document.getElementById('login-success').textContent = 'Connexion réussie !';
        console.log('Tentative de connexion avec:', { username, password });
    }
});