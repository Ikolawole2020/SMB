// Enhanced Animation System for Add Bank Account Page with Save Functionality
document.addEventListener('DOMContentLoaded', function() {
    const accountNumberInput = document.getElementById('account_number');
    const bankCodeSelect = document.getElementById('bank_code');
    const accountNameInput = document.getElementById('account_name');
    const bvnInput = document.getElementById('bvn');
    const loadingOverlay = document.createElement('div');
    const form = document.getElementById('bankAccountForm');

    // Store verification data
    let verifiedData = null;

    // Create loading overlay
    loadingOverlay.id = 'loading-overlay';
    loadingOverlay.className = 'loading-overlay';
    loadingOverlay.innerHTML = `
        <div class="spinner-container">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2 mb-0" id="loading-text">Verifying account details...</p>
        </div>
    `;
    document.body.appendChild(loadingOverlay);

    // Enhanced verification function
    async function verifyAccountDetails() {
        const accountNumber = accountNumberInput.value.trim();
        const bankCode = bankCodeSelect.value;

        if (!accountNumber || !bankCode || accountNumber.length < 10) {
            return;
        }

        // Show loading animation
        loadingOverlay.style.display = 'flex';
        document.getElementById('loading-text').textContent = 'Verifying account details...';
        accountNumberInput.classList.add('verifying');

        try {
            const response = await fetch('/api/verify-account', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ account_number: accountNumber, bank_code: bankCode })
            });

            const data = await response.json();

            if (data.status === 'success') {
                // Success animation
                accountNameInput.value = data.account_name;
                accountNameInput.classList.add('highlight-success');
                accountNameInput.readOnly = true;

                // Store verified data
                verifiedData = {
                    account_number: accountNumber,
                    bank_code: bankCode,
                    account_name: data.account_name,
                    bank_name: bankCodeSelect.options[bankCodeSelect.selectedIndex].text
                };

                // Enable save button
                enableSaveButton();

                // Success message
                showNotification('Account verified successfully! Click "Save Account" to add it to your profile.', 'success');
            } else {
                // Error handling
                accountNameInput.value = '';
                verifiedData = null;
                disableSaveButton();
                showNotification('Account verification failed', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            accountNameInput.value = '';
            verifiedData = null;
            disableSaveButton();
            showNotification('Network error. Please try again.', 'error');
        } finally {
            loadingOverlay.style.display = 'none';
            accountNumberInput.classList.remove('verifying');
        }
    }

    // Save verified account
    async function saveVerifiedAccount() {
        if (!verifiedData) {
            showNotification('Please verify your account first', 'error');
            return;
        }

        // Add BVN if provided
        if (bvnInput && bvnInput.value.trim()) {
            verifiedData.bvn = bvnInput.value.trim();
        }

        loadingOverlay.style.display = 'flex';
        document.getElementById('loading-text').textContent = 'Saving bank account...';

        try {
            const response = await fetch('/api/save-verified-account', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(verifiedData)
            });

            const data = await response.json();

            if (data.success) {
                showNotification(data.message, 'success');

                // Disable form inputs
                accountNumberInput.disabled = true;
                bankCodeSelect.disabled = true;
                accountNameInput.disabled = true;
                if (bvnInput) bvnInput.disabled = true;

                // Redirect after delay
                setTimeout(() => {
                    window.location.href = data.redirect_url;
                }, 2000);

            } else {
                showNotification(data.error || 'Failed to save account', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Network error. Please try again.', 'error');
        } finally {
            loadingOverlay.style.display = 'none';
        }
    }

    // Create save button
    function createSaveButton() {
        const saveButton = document.createElement('button');
        saveButton.type = 'button';
        saveButton.id = 'save-verified-account';
        saveButton.className = 'btn btn-success btn-lg w-100 mt-3';
        saveButton.innerHTML = '<i class="fas fa-save me-2"></i>Save Verified Account';
        saveButton.style.display = 'none';
        saveButton.onclick = saveVerifiedAccount;

        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.parentNode.insertBefore(saveButton, submitButton);
        }

        return saveButton;
    }

    const saveButton = createSaveButton();

    function enableSaveButton() {
        if (saveButton) {
            saveButton.style.display = 'block';
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.style.display = 'none';
            }
        }
    }

    function disableSaveButton() {
        if (saveButton) {
            saveButton.style.display = 'none';
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.style.display = 'block';
            }
        }
    }

    // Enhanced notification system
    function showNotification(message, type) {
        // Remove existing notifications
        const existingNotifications = document.querySelectorAll('.alert');
        existingNotifications.forEach(notification => notification.remove());

        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show`;
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '9999';
        notification.style.minWidth = '300px';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        document.body.appendChild(notification);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    // Enhanced event listeners
    accountNumberInput.addEventListener('blur', verifyAccountDetails);
    bankCodeSelect.addEventListener('change', verifyAccountDetails);

    // Add CSS for animations
    const style = document.createElement('style');
    style.textContent = `
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 9999;
        }
        
        .spinner-container {
            background: white;
            padding: 2rem;
            border-radius: 0.5rem;
            text-align: center;
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
        }
        
        .highlight-success {
            background-color: #d4edda !important;
            border-color: #c3e6cb !important;
            transition: all 0.3s ease;
        }
        
        .verifying {
            animation: pulse 1.5s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
    `;
    document.head.appendChild(style);

    // Handle form submission prevention
    if (form) {
        form.addEventListener('submit', function(e) {
            if (verifiedData) {
                e.preventDefault();
                saveVerifiedAccount();
            }
        });
    }
});