// Currency Rates and Conversion for Scanovich.ai
// Updated: 2025-07-30 with real-time API integration

const currencyRates = {
    // Базовая валюта - рубли (RUB)
    base: 'RUB',
    
    // Актуальные курсы (обновляются автоматически через API)
    rates: {
        'RUB': 1.0,           // Российский рубль (базовая)
        'USD': 0.011,         // Доллар США (~90 руб за 1 USD)
        'THB': 0.38,          // Тайский бат (~2.6 руб за 1 THB)  
        'KZT': 0.20           // Казахский тенге (~5 руб за 1 KZT)
    },
    
    // Последнее обновление курсов
    lastUpdated: null,
    
    // Конфигурация валют по языкам
    currencies: {
        'ru': { code: 'RUB', symbol: '₽', name: 'рублей' },
        'en': { code: 'USD', symbol: '$', name: 'USD' },
        'th': { code: 'THB', symbol: '฿', name: 'บาท' },
        'kk': { code: 'KZT', symbol: '₸', name: 'теңге' }
    },
    
    // API конфигурация для получения актуальных курсов
    api: {
        // Используем бесплатный API exchangerate-api.com 
        baseUrl: 'https://api.exchangerate-api.com/v4/latest',
        fallbackUrl: 'https://api.fixer.io/latest', // резервный API
        timeout: 5000, // таймаут 5 секунд
        updateInterval: 3600000, // обновление каждый час (3600000 мс)
    }
};

// Функция получения курсов через API
async function fetchExchangeRates() {
    try {
        console.log('🔄 Получение актуальных курсов валют...');
        
        // Получаем курсы USD относительно других валют
        const response = await fetch(`${currencyRates.api.baseUrl}/USD`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Конвертируем курсы в рубли как базовую валюту
        const usdToRub = data.rates.RUB || 90; // fallback к 90 руб за доллар
        const thbToUsd = data.rates.THB || 33; // Тайских батов за доллар
        const kztToUsd = data.rates.KZT || 450; // Казахских тенге за доллар
        
        // Обновляем курсы (из рублей в другие валюты)
        currencyRates.rates.USD = 1 / usdToRub;
        currencyRates.rates.THB = thbToUsd / usdToRub;
        currencyRates.rates.KZT = kztToUsd / usdToRub;
        currencyRates.lastUpdated = new Date();
        
        console.log('✅ Курсы валют обновлены:', currencyRates.rates);
        console.log('📅 Время обновления:', currencyRates.lastUpdated.toLocaleString('ru-RU'));
        
        return true;
        
    } catch (error) {
        console.warn('⚠️ Ошибка получения курсов валют:', error.message);
        console.log('📝 Используются резервные курсы');
        return false;
    }
}

// Конвертация валют
function convertCurrency(amount, fromCurrency, toCurrency) {
    if (fromCurrency === toCurrency) return amount;
    
    // Конвертируем через базовую валюту (RUB)
    const baseAmount = fromCurrency === 'RUB' ? amount : amount / currencyRates.rates[fromCurrency];
    const targetAmount = toCurrency === 'RUB' ? baseAmount : baseAmount * currencyRates.rates[toCurrency];
    
    return Math.round(targetAmount);
}

// Форматирование валют с правильными разделителями
function formatCurrencyAdvanced(amount, lang) {
    const currency = currencyRates.currencies[lang] || currencyRates.currencies['ru'];
    
    // Конвертируем из рублей в целевую валюту
    const convertedAmount = convertCurrency(amount, 'RUB', currency.code);
    
    // Форматирование чисел с разделителями
    const formatted = new Intl.NumberFormat(getLocaleByLang(lang)).format(convertedAmount);
    
    return `${formatted} ${currency.symbol}`;
}

// Получение локали по языку
function getLocaleByLang(lang) {
    const locales = {
        'ru': 'ru-RU',
        'en': 'en-US', 
        'th': 'th-TH',
        'kk': 'kk-KZ'
    };
    return locales[lang] || 'ru-RU';
}

// Функция для автоматического обновления курсов
async function updateCurrencyRates() {
    const now = new Date();
    const lastUpdate = currencyRates.lastUpdated;
    
    // Проверяем, нужно ли обновлять курсы
    if (!lastUpdate || (now - lastUpdate) > currencyRates.api.updateInterval) {
        await fetchExchangeRates();
    } else {
        console.log('📊 Курсы валют актуальны');
    }
}

// Инициализация при загрузке страницы
function initCurrencyRates() {
    console.log('💰 Инициализация системы валютных курсов...');
    
    // Получаем актуальные курсы
    updateCurrencyRates();
    
    // Настраиваем автоматическое обновление каждый час
    setInterval(updateCurrencyRates, currencyRates.api.updateInterval);
    
    console.log('✅ Система валютных курсов готова');
}

// Экспорт для использования в других скриптах
if (typeof window !== 'undefined') {
    window.currencyRates = currencyRates;
    window.convertCurrency = convertCurrency;
    window.formatCurrencyAdvanced = formatCurrencyAdvanced;
    window.updateCurrencyRates = updateCurrencyRates;
    window.fetchExchangeRates = fetchExchangeRates;
    window.initCurrencyRates = initCurrencyRates;
    
    // Автоматическая инициализация при загрузке DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCurrencyRates);
    } else {
        initCurrencyRates();
    }
} 