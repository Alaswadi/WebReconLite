/**
 * WebReconLite - Main JavaScript
 * Cyberpunk-themed web reconnaissance tool
 */

document.addEventListener('DOMContentLoaded', function() {
    // Apply glitch text effect
    const glitchTexts = document.querySelectorAll('.glitch-text');
    glitchTexts.forEach(text => {
        text.setAttribute('data-text', text.textContent);
    });
    
    // Initialize modals
    const modals = document.querySelectorAll('.modal');
    const closeButtons = document.querySelectorAll('.close-button');
    
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            if (modal) {
                modal.style.display = 'none';
            }
        });
    });
    
    window.addEventListener('click', function(event) {
        modals.forEach(modal => {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
    });
    
    // Form input effects
    const formInputs = document.querySelectorAll('input[type="text"]');
    formInputs.forEach(input => {
        input.addEventListener('focus', function() {
            const border = this.nextElementSibling;
            if (border && border.classList.contains('input-border')) {
                border.style.width = '100%';
            }
        });
        
        input.addEventListener('blur', function() {
            const border = this.nextElementSibling;
            if (border && border.classList.contains('input-border')) {
                border.style.width = '0';
            }
        });
    });
    
    // Add cyberpunk cursor effect
    const cursorEffect = document.createElement('div');
    cursorEffect.classList.add('cursor-effect');
    document.body.appendChild(cursorEffect);
    
    document.addEventListener('mousemove', function(e) {
        cursorEffect.style.left = e.clientX + 'px';
        cursorEffect.style.top = e.clientY + 'px';
    });
    
    // Add random glitch effects to elements
    function addRandomGlitchEffect() {
        const elements = document.querySelectorAll('.neon-text, .lite-text, .btn');
        const randomElement = elements[Math.floor(Math.random() * elements.length)];
        
        if (randomElement) {
            randomElement.classList.add('glitch-active');
            
            setTimeout(() => {
                randomElement.classList.remove('glitch-active');
            }, 200);
        }
        
        // Schedule next glitch
        const nextGlitchTime = 3000 + Math.random() * 5000;
        setTimeout(addRandomGlitchEffect, nextGlitchTime);
    }
    
    // Start random glitch effects
    setTimeout(addRandomGlitchEffect, 3000);
    
    // Add terminal typing effect to any element with class 'typing-effect'
    const typingElements = document.querySelectorAll('.typing-effect');
    
    typingElements.forEach(element => {
        const text = element.textContent;
        element.textContent = '';
        
        let i = 0;
        const typingInterval = setInterval(() => {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
            } else {
                clearInterval(typingInterval);
                element.classList.add('typing-done');
            }
        }, 50);
    });
});
