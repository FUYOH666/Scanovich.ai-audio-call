// Main JavaScript for Scanovich.ai Website - ПОЛНАЯ ПЕРЕРАБОТКА

// Currency exchange rates (updated periodically)
const exchangeRates = {
    USD: 95, // 1 USD = 95 RUB  
    THB: 2.8, // 1 THB = 2.8 RUB
    RUB: 1
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initTranslations();
    initCalculator();
    initScrollEffects();
    initFormHandling();
    initMobileMenu();
    
    // Add fade-in animations
    observeElements();
});

// Smooth scroll function
function scrollTo(selector) {
    const element = document.querySelector(selector);
    if (element) {
        element.scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Calculator functionality - ПОЛНОСТЬЮ ПЕРЕПИСАН
function initCalculator() {
    // Add event listeners to all sliders
    const callsSlider = document.getElementById('callsSlider');
    const salarySlider = document.getElementById('salarySlider');
    const timeSlider = document.getElementById('timeSlider');
    
    if (callsSlider) {
        callsSlider.addEventListener('input', function() {
            document.getElementById('callsValue').textContent = formatNumber(this.value);
            updateCalculator();
        });
    }
    
    if (salarySlider) {
        salarySlider.addEventListener('input', function() {
            const salary = parseInt(this.value);
            document.getElementById('salaryValue').textContent = formatCurrency(salary, currentLang);
            updateCalculator();
        });
    }
    
    if (timeSlider) {
        timeSlider.addEventListener('input', function() {
            document.getElementById('timeValue').textContent = parseFloat(this.value);
            updateCalculator();
        });
    }
    
    // Initial calculation
    updateCalculator();
}

function updateCalculator() {
    const callsSlider = document.getElementById('callsSlider');
    const salarySlider = document.getElementById('salarySlider');
    const timeSlider = document.getElementById('timeSlider');
    
    if (!callsSlider || !salarySlider || !timeSlider) return;
    
    const calls = parseInt(callsSlider.value);
    const salary = parseInt(salarySlider.value);
    const timePerCall = parseFloat(timeSlider.value);
    
    // РАСЧЕТЫ В РУБЛЯХ (база)
    // Формула с учетом времени анализа: базовая производительность 217.4 звонка/день при 2.5 мин на звонок
    const baseTimePerCall = 2.5; // базовое время в минутах
    const timeMultiplier = timePerCall / baseTimePerCall; // коэффициент времени
    const callsPerAnalyst = 217.4 / timeMultiplier; // корректировка по времени
    
    const analystsNeeded = Math.ceil(calls / callsPerAnalyst);
    const yearlySalaryCost = analystsNeeded * salary * 12;
    const managementCost = Math.round(yearlySalaryCost * 0.25); // 25% на менеджмент
    const hrCost = Math.round(yearlySalaryCost * 0.20); // 20% на HR, рекрутинг, обучение  
    const officeCost = Math.round(analystsNeeded * 180000); // 180k на аналитика (офис, оборудование, ПО)
    const risksCost = Math.round(yearlySalaryCost * 0.18); // 18% на больничные, отпуска, текучку
    
    const totalHumanCost = yearlySalaryCost + managementCost + hrCost + officeCost + risksCost;
    
    // AI system cost calculation - 299k рублей в месяц
    const baseAiMonthlyCost = Math.max(299000, calls * 60); // 299k базовая стоимость или 60 руб за звонок в месяц
    const aiYearlyCost = baseAiMonthlyCost * 12;
    
    const totalSavings = totalHumanCost - aiYearlyCost;
    const roi = Math.round((totalSavings / 900000) * 100); // ROI на базе 900k средних инвестиций
    
    // КОНВЕРТАЦИЯ ВАЛЮТ по текущему языку
    const currency = getCurrencyByLang(currentLang);
    const rate = exchangeRates[currency];
    
    // Обновляем интерфейс с конвертированными значениями
    updateElement('analystsCount', analystsNeeded + ' ' + getAnalystsWord(analystsNeeded, currentLang));
    updateElement('totalSalaries', formatCurrency(yearlySalaryCost / 12 / rate, currentLang) + getMonthLabel(currentLang));
    updateElement('managementCost', formatCurrency(managementCost / 12 / rate, currentLang) + getMonthLabel(currentLang));
    updateElement('hrCost', formatCurrency(hrCost / 12 / rate, currentLang) + getMonthLabel(currentLang));
    updateElement('officeCost', formatCurrency(officeCost / 12 / rate, currentLang) + getMonthLabel(currentLang));
    updateElement('risksCost', formatCurrency(risksCost / 12 / rate, currentLang) + getMonthLabel(currentLang));
    updateElement('totalHumanCost', formatCurrency(totalHumanCost / 12 / rate, currentLang) + getMonthLabel(currentLang));
    
    updateElement('softwareCost', formatCurrency(baseAiMonthlyCost / rate, currentLang) + getMonthLabel(currentLang));
    updateElement('totalAiCost', formatCurrency(aiYearlyCost / rate, currentLang) + getYearLabel(currentLang));
    updateElement('monthlySavings', formatCurrency(totalSavings / 12 / rate, currentLang));
    updateElement('yearlySavings', formatCurrency(totalSavings / rate, currentLang));
    updateElement('roiValue', roi + '%');
}

// Utility functions
function getCurrencyByLang(lang) {
    switch(lang) {
        case 'en': return 'USD';
        case 'th': return 'THB';
        default: return 'RUB';
    }
}

function getCurrencySymbol(lang) {
    switch(lang) {
        case 'en': return '$';
        case 'th': return '฿';
        default: return '₽';
    }
}

function getAnalystsWord(count, lang) {
    if (lang === 'en') {
        return count === 1 ? 'analyst' : 'analysts';
    } else if (lang === 'th') {
        return 'คน';
    } else {
        // Russian
        if (count % 10 === 1 && count % 100 !== 11) {
            return 'человек';
        } else if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) {
            return 'человека';
        } else {
            return 'человек';
        }
    }
}

function getMonthLabel(lang) {
    switch(lang) {
        case 'en': return '/month';
        case 'th': return '/เดือน';
        default: return '/мес';
    }
}

function getYearLabel(lang) {
    switch(lang) {
        case 'en': return '/year';
        case 'th': return '/ปี';
        default: return '/год';
    }
}

function formatCurrency(amount, lang) {
    const symbol = getCurrencySymbol(lang);
    const formatted = new Intl.NumberFormat().format(Math.round(amount));
    
    if (lang === 'en') {
        return symbol + formatted;
    } else {
        return formatted + ' ' + symbol;
    }
}

function formatNumber(num) {
    return new Intl.NumberFormat().format(num);
}

function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

// Form handling
function initFormHandling() {
    const form = document.querySelector('.contact-form');
    if (form) {
        form.addEventListener('submit', submitForm);
    }
}

function submitForm(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData);
    
    // Здесь должна быть отправка в Telegram (как было раньше)
    console.log('Form submitted:', data);
    
    // Показываем сообщение об успехе
    if (currentLang === 'ru') {
        alert('Спасибо! Ваша заявка отправлена. Мы свяжемся с вами в течение 24 часов.');
    } else if (currentLang === 'en') {
        alert('Thank you! Your request has been sent. We will contact you within 24 hours.');
    } else {
        alert('ขอบคุณ! คำขอของคุณถูกส่งแล้ว เราจะติดต่อกลับภายใน 24 ชั่วโมง');
    }
    
    event.target.reset();
}

// Scroll effects
function initScrollEffects() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, observerOptions);
    
    // Observe all sections
    document.querySelectorAll('section').forEach(section => {
        observer.observe(section);
    });
}

function observeElements() {
    // Добавляем анимации появления
    const elements = document.querySelectorAll('.feature-card, .magnet-card, .result-section');
    elements.forEach((el, index) => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'all 0.6s ease';
        el.style.transitionDelay = (index * 0.1) + 's';
        
        setTimeout(() => {
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        }, 100 + (index * 100));
    });
}

// Mobile Menu Functions
function initMobileMenu() {
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const nav = document.querySelector('.nav');
    
    if (mobileMenuToggle && nav) {
        // Close menu when clicking overlay
        nav.addEventListener('click', function(e) {
            if (e.target === nav && nav.classList.contains('open')) {
                closeMobileMenu();
            }
        });
        
        // Close menu on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && nav.classList.contains('open')) {
                closeMobileMenu();
            }
        });
        
        // Close menu when screen size changes to desktop
        window.addEventListener('resize', function() {
            if (window.innerWidth > 768 && nav.classList.contains('open')) {
                closeMobileMenu();
            }
        });
    }
}

function toggleMobileMenu() {
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const nav = document.querySelector('.nav');
    
    if (mobileMenuToggle && nav) {
        mobileMenuToggle.classList.toggle('active');
        nav.classList.toggle('open');
        
        // Prevent body scrolling when menu is open
        if (nav.classList.contains('open')) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = '';
        }
    }
}

function closeMobileMenu() {
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const nav = document.querySelector('.nav');
    
    if (mobileMenuToggle && nav) {
        mobileMenuToggle.classList.remove('active');
        nav.classList.remove('open');
        document.body.style.overflow = '';
    }
}

// Export functions for external use
window.scrollTo = scrollTo;
window.updateCalculator = updateCalculator;
window.submitForm = submitForm;
window.toggleMobileMenu = toggleMobileMenu;
window.closeMobileMenu = closeMobileMenu;