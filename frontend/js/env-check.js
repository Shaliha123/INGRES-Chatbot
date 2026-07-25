if (window.location.protocol === 'file:') {
    const showWarning = () => {
        const warning = document.createElement('div');
        warning.style.cssText = 'position:fixed;top:0;left:0;right:0;background:#ef4444;color:white;padding:10px;text-align:center;z-index:10000;font-size:13px;font-weight:bold;line-height:1.5;';
        warning.innerHTML = '⚠️ Firebase Auth requires a local web server (for example VS Code Live Server or any localhost server). Opening the page via file:// will not work for login and registration.';
        document.body.prepend(warning);

        document.querySelectorAll('form').forEach(form => {
            form.querySelectorAll('input, button, select, textarea').forEach(el => {
                el.disabled = true;
            });
        });
    };

    if (document.body) {
        showWarning();
    } else {
        window.addEventListener('DOMContentLoaded', showWarning);
    }
}
