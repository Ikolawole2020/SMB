// Deposit functionality with Paystack integration
document.addEventListener('DOMContentLoaded', function() {
    const depositForm = document.querySelector('form[action*="deposit"]');

    if (depositForm) {
        depositForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const submitBtn = this.querySelector('button[type="submit"]');

            // Show loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

            try {
                const response = await fetch(this.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                const data = await response.json();

                if (data.status === 'success') {
                    // Redirect to Paystack payment page
                    window.location.href = data.authorization_url;
                } else {
                    // Show error message
                    showAlert(data.message || 'Payment initialization failed', 'error');
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = 'Deposit';
                }
            } catch (error) {
                console.error('Error:', error);
                showAlert('An error occurred. Please try again.', 'error');
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Deposit';
            }
        });
    }

    // Handle Paystack callback
    const urlParams = new URLSearchParams(window.location.search);
    const reference = urlParams.get('reference');
    const trxref = urlParams.get('trxref');

    if (reference || trxref) {
        verifyPayment(reference || trxref);
    }
});

// Verify payment with backend
async function verifyPayment(reference) {
    try {
        const response = await fetch(`/api/verify-payment/${reference}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        const data = await response.json();

        if (data.status === 'success') {
            showAlert('Payment successful! Your deposit has been processed.', 'success');
            setTimeout(() => {
                window.location.href = '/transactions';
            }, 2000);
        } else {
            showAlert('Payment verification failed. Please contact support.', 'error');
        }
    } catch (error) {
        console.error('Error verifying payment:', error);
        showAlert('Error verifying payment. Please contact support.', 'error');
    }
}

// Show alert messages
function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    const container = document.querySelector('.card-body');
    container.insertBefore(alertDiv, container.firstChild);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Format currency input
function formatCurrency(input) {
    let value = input.value.replace(/[^\d]/g, '');
    if (value) {
        value = parseInt(value, 10);
        input.value = (value / 100).toFixed(2);
    }
}