document.addEventListener('DOMContentLoaded', function() {
    let currentStep = 1;
    const formSteps = document.querySelectorAll('.form-step');
    const progressSteps = document.querySelectorAll('.progress-step');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');

    function changeStep(step) {
        // Valider l'étape actuelle
        console.log(`Changement d'étape : ${step}`); // Débogage

        if (step === 1 && !validateStep(currentStep)) {
            return;
        }

        // Masquer l'étape actuelle
        formSteps[currentStep - 1].classList.remove('active');
        progressSteps[currentStep - 1].classList.remove('active');

        // Mettre à jour l'étape actuelle
        currentStep += step;

        // Afficher la nouvelle étape
        formSteps[currentStep - 1].classList.add('active');
        progressSteps[currentStep - 1].classList.add('active');

        // Mettre à jour la visibilité des boutons
        updateButtonVisibility();
    }

    function updateButtonVisibility() {
        if (currentStep === formSteps.length) {
            nextBtn.style.display = 'none';
            submitBtn.style.display = 'inline-block';
        } else {
            nextBtn.style.display = 'inline-block';
            submitBtn.style.display = 'none';
        }

        prevBtn.style.display = currentStep === 1 ? 'none' : 'inline-block';
    }

    function validateStep(step) {
        const inputs = document.querySelectorAll(`.form-step[data-step="${step}"] input, .form-step[data-step="${step}"] select, .form-step[data-step="${step}"] textarea`);
        let valid = true;
        let errorMessage = '';
    
        inputs.forEach(input => {
            if (input.hasAttribute('required') && !input.value) {
                valid = false;
                input.classList.add('error');
                errorMessage += `<p>${input.previousElementSibling.textContent} est requis.</p>`;
                console.log(`${input.name} est requis mais n'a pas été rempli.`); // Débogage
            } else {
                input.classList.remove('error');
            }
        });
    
        if (!valid) {
            Swal.fire({
                icon: 'error',
                title: 'Erreur de validation',
                html: errorMessage,
                showConfirmButton: true
            });
        } else {
            console.log('Validation réussie pour cette étape.');
        }
    
        return valid;
    }
    

    // Écouteurs d'événements
    prevBtn.addEventListener('click', () => changeStep(-1));
    nextBtn.addEventListener('click', () => changeStep(1));

    // Initialiser le formulaire
    updateButtonVisibility();
});
