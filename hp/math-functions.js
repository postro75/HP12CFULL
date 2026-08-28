/**
 * HP-12C Mathematical Functions Engine
 * 
 * Implements basic and advanced mathematical operations:
 * - Percentage calculations (%, %T, Δ%)
 * - Reciprocal (1/x)
 * - Power and roots (yˣ, √x)
 * - Logarithms and exponentials (LN, eˣ)
 * - Integer and fractional parts (INTG, FRAC)
 * 
 * @version 1.0
 */

class MathEngine {
    constructor() {
        // Mathematical constants
        this.E = Math.E;         // Euler's number (2.71828...)
        this.PI = Math.PI;       // Pi (3.14159...)
        this.MAX_VALUE = 9.999999999e99;  // HP-12C max value
        this.MIN_VALUE = 1e-99;  // HP-12C min value (positive)
    }

    /**
     * Calculate percentage: X is what percent of Y
     * Formula: (X / Y) × 100
     * @param {number} x - Amount
     * @param {number} y - Base
     * @returns {number} Percentage
     */
    percent(x, y) {
        if (y === 0) {
            throw new Error('Error 0'); // Division by zero
        }
        return (x / y) * 100;
    }

    /**
     * Calculate percentage of total: X% of Y
     * Formula: (X / 100) × Y
     * @param {number} x - Percentage
     * @param {number} y - Base
     * @returns {number} Amount
     */
    percentTotal(x, y) {
        return (x / 100) * y;
    }

    /**
     * Calculate percentage change from Y to X
     * Formula: ((X - Y) / Y) × 100
     * @param {number} x - New value
     * @param {number} y - Old value
     * @returns {number} Percentage change
     */
    deltaPercent(x, y) {
        if (y === 0) {
            throw new Error('Error 0'); // Division by zero
        }
        return ((x - y) / y) * 100;
    }

    /**
     * Calculate reciprocal: 1 / X
     * @param {number} x - Value
     * @returns {number} Reciprocal
     */
    reciprocal(x) {
        if (x === 0) {
            throw new Error('Error 0'); // Division by zero
        }
        return 1 / x;
    }

    /**
     * Calculate power: Y raised to the power of X (Y^X)
     * @param {number} y - Base
     * @param {number} x - Exponent
     * @returns {number} Result
     */
    power(y, x) {
        // Handle special cases
        if (y === 0 && x === 0) {
            throw new Error('Error 0'); // 0^0 is undefined
        }
        
        if (y === 0 && x < 0) {
            throw new Error('Error 0'); // 0^negative is undefined
        }
        
        if (y < 0 && x !== Math.floor(x)) {
            throw new Error('Error 0'); // Negative base with fractional exponent
        }
        
        const result = Math.pow(y, x);
        
        // Check for overflow/underflow
        if (!isFinite(result)) {
            throw new Error('Error 9'); // Overflow
        }
        
        if (result > this.MAX_VALUE) {
            throw new Error('Error 9'); // Overflow
        }
        
        return result;
    }

    /**
     * Calculate square root: √X
     * @param {number} x - Value
     * @returns {number} Square root
     */
    sqrt(x) {
        if (x < 0) {
            throw new Error('Error 0'); // Square root of negative
        }
        return Math.sqrt(x);
    }

    /**
     * Calculate natural logarithm: ln(X)
     * @param {number} x - Value
     * @returns {number} Natural logarithm
     */
    ln(x) {
        if (x <= 0) {
            throw new Error('Error 0'); // Log of non-positive number
        }
        return Math.log(x);
    }

    /**
     * Calculate exponential: e^X
     * @param {number} x - Exponent
     * @returns {number} e raised to power X
     */
    exp(x) {
        const result = Math.exp(x);
        
        if (!isFinite(result)) {
            throw new Error('Error 9'); // Overflow
        }
        
        if (result > this.MAX_VALUE) {
            throw new Error('Error 9'); // Overflow
        }
        
        return result;
    }

    /**
     * Get integer part of X
     * @param {number} x - Value
     * @returns {number} Integer part
     */
    integerPart(x) {
        return Math.trunc(x);
    }

    /**
     * Get fractional part of X
     * @param {number} x - Value
     * @returns {number} Fractional part
     */
    fractionalPart(x) {
        return x - Math.trunc(x);
    }

    /**
     * Multiply by 12 (for financial calculations)
     * @param {number} x - Value
     * @returns {number} X × 12
     */
    multiply12(x) {
        return x * 12;
    }

    /**
     * Divide by 12 (for financial calculations)
     * @param {number} x - Value
     * @returns {number} X ÷ 12
     */
    divide12(x) {
        return x / 12;
    }

    /**
     * Calculate factorial: n!
     * @param {number} n - Non-negative integer
     * @returns {number} Factorial
     */
    factorial(n) {
        if (n < 0 || n !== Math.floor(n)) {
            throw new Error('Error 0'); // Factorial requires non-negative integer
        }
        
        if (n > 69) {
            throw new Error('Error 9'); // Factorial overflow (70! exceeds range)
        }
        
        if (n === 0 || n === 1) {
            return 1;
        }
        
        let result = 1;
        for (let i = 2; i <= n; i++) {
            result *= i;
        }
        
        return result;
    }

    /**
     * Absolute value
     * @param {number} x - Value
     * @returns {number} |X|
     */
    abs(x) {
        return Math.abs(x);
    }

    /**
     * Round to current display precision
     * Used by RND function (f PMT)
     * @param {number} x - Value to round
     * @param {number} decimals - Number of decimal places
     * @returns {number} Rounded value
     */
    round(x, decimals = 2) {
        const factor = Math.pow(10, decimals);
        return Math.round(x * factor) / factor;
    }
}
