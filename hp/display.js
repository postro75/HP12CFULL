/**
 * HP-12C Display Manager
 * Handles number formatting and LED display visualization
 */

class DisplayManager {
    constructor() {
        this.format = 'fixed';    // 'fixed', 'sci', 'eng'
        this.decimals = 2;        // Number of decimal places
        this.maxDigits = 10;      // Maximum display digits
        this.displayElement = null;
        this.indicatorElements = {};
    }

    /**
     * Initialize display with DOM elements
     * @param {HTMLElement} displayElement - Main display element
     * @param {object} indicators - Object mapping indicator names to elements
     */
    initialize(displayElement, indicators = {}) {
        this.displayElement = displayElement;
        this.indicatorElements = indicators;
        this.show(0);
    }

    /**
     * Format and display a number
     * @param {number} value - Number to display
     * @param {boolean} flash - Whether to flash the display
     */
    show(value, flash = false) {
        if (!this.displayElement) return;

        const formatted = this.formatNumber(value);
        this.displayElement.textContent = formatted;

        if (flash) {
            this.displayElement.classList.add('flash');
            setTimeout(() => {
                this.displayElement.classList.remove('flash');
            }, 100);
        }
    }

    /**
     * Format number according to current display format
     * @param {number} value - Number to format
     * @returns {string} Formatted number string
     */
    formatNumber(value) {
        // Handle special cases
        if (value === null || value === undefined) return '0.';
        if (!isFinite(value)) return 'Error 0';
        if (isNaN(value)) return 'Error 0';

        // Handle very large or very small numbers
        const absValue = Math.abs(value);
        if (absValue > 9.999999999e99) return value < 0 ? '-9.999999999 99' : '9.999999999 99';
        if (absValue < 1e-99 && absValue !== 0) return '0.';

        switch (this.format) {
            case 'sci':
                return this.formatScientific(value);
            case 'eng':
                return this.formatEngineering(value);
            case 'fixed':
            default:
                return this.formatFixed(value);
        }
    }

    /**
     * Format number in fixed-point notation
     * @param {number} value - Number to format
     * @returns {string} Formatted string
     */
    formatFixed(value) {
        // Check if number is too large for fixed format
        const integerDigits = Math.floor(Math.abs(value)).toString().length;
        if (integerDigits > this.maxDigits) {
            return this.formatScientific(value);
        }

        // Round to specified decimal places
        const factor = Math.pow(10, this.decimals);
        const rounded = Math.round(value * factor) / factor;

        // Format with fixed decimal places
        let formatted = rounded.toFixed(this.decimals);

        // Ensure not too many digits
        if (formatted.replace(/[^0-9]/g, '').length > this.maxDigits) {
            return this.formatScientific(value);
        }

        // HP-12C always shows decimal point
        if (!formatted.includes('.')) {
            formatted += '.';
        }

        return formatted;
    }

    /**
     * Format number in scientific notation
     * @param {number} value - Number to format
     * @returns {string} Formatted string (e.g., "1.234567890 -12")
     */
    formatScientific(value) {
        if (value === 0) return '0.';

        const exp = Math.floor(Math.log10(Math.abs(value)));
        const mantissa = value / Math.pow(10, exp);

        // Format mantissa with up to 9 decimal places
        let mantissaStr = mantissa.toFixed(9);
        
        // Remove trailing zeros after decimal point
        mantissaStr = mantissaStr.replace(/\.?0+$/, '');
        
        // Ensure decimal point
        if (!mantissaStr.includes('.')) {
            mantissaStr += '.';
        }

        // Format exponent (HP-12C shows space before exponent)
        const expStr = exp >= 0 ? ` ${exp}` : ` ${exp}`;

        return mantissaStr + expStr;
    }

    /**
     * Format number in engineering notation (exponent multiple of 3)
     * @param {number} value - Number to format
     * @returns {string} Formatted string
     */
    formatEngineering(value) {
        if (value === 0) return '0.';

        const exp = Math.floor(Math.log10(Math.abs(value)));
        const engExp = Math.floor(exp / 3) * 3;
        const mantissa = value / Math.pow(10, engExp);

        let mantissaStr = mantissa.toFixed(9);
        mantissaStr = mantissaStr.replace(/\.?0+$/, '');
        
        if (!mantissaStr.includes('.')) {
            mantissaStr += '.';
        }

        const expStr = engExp >= 0 ? ` ${engExp}` : ` ${engExp}`;

        return mantissaStr + expStr;
    }

    /**
     * Set display format
     * @param {string} format - 'fixed', 'sci', or 'eng'
     * @param {number} decimals - Number of decimal places (for fixed)
     */
    setFormat(format, decimals = null) {
        this.format = format;
        if (decimals !== null && format === 'fixed') {
            this.decimals = Math.max(0, Math.min(9, decimals));
        }
    }

    /**
     * Show error message
     * @param {string} message - Error message
     */
    showError(message = 'Error 0') {
        if (!this.displayElement) return;

        this.displayElement.textContent = message;
        this.displayElement.classList.add('error');
        
        setTimeout(() => {
            this.displayElement.classList.remove('error');
        }, 400);
    }

    /**
     * Set indicator state
     * @param {string} name - Indicator name (e.g., 'f', 'g', 'USER')
     * @param {boolean} active - Whether indicator should be active
     */
    setIndicator(name, active) {
        const element = this.indicatorElements[name];
        if (element) {
            if (active) {
                element.classList.add('active');
            } else {
                element.classList.remove('active');
            }
        }
    }

    /**
     * Update stack display (optional debug feature)
     * @param {object} stack - Stack state object
     */
    updateStackDisplay(stack) {
        const stackT = document.getElementById('stackT');
        const stackZ = document.getElementById('stackZ');
        const stackY = document.getElementById('stackY');

        if (stackT) stackT.textContent = this.formatNumber(stack.t);
        if (stackZ) stackZ.textContent = this.formatNumber(stack.z);
        if (stackY) stackY.textContent = this.formatNumber(stack.y);
    }

    /**
     * Clear display
     */
    clear() {
        this.show(0);
    }

    /**
     * Get current format settings
     * @returns {object} Format settings
     */
    getFormat() {
        return {
            format: this.format,
            decimals: this.decimals
        };
    }
}
