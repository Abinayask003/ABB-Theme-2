document.addEventListener("DOMContentLoaded", () => {
    const singleRadio = document.querySelector('input[value="single"]');
    const batchRadio = document.querySelector('input[value="batch"]');
    const singleInput = document.getElementById('single_input');
    const batchInput = document.getElementById('batch_input');

    // Show single input by default
    singleInput.style.display = singleRadio.checked ? 'block' : 'none';
    batchInput.style.display = batchRadio.checked ? 'block' : 'none';

    // Toggle inputs when radio changes
    singleRadio.addEventListener('change', () => {
        singleInput.style.display = 'block';
        batchInput.style.display = 'none';
    });

    batchRadio.addEventListener('change', () => {
        singleInput.style.display = 'none';
        batchInput.style.display = 'block';
    });
});
