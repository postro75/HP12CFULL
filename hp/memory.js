/**
 * HP-12C Memory Manager
 * Manages 20 storage registers (R0-R19)
 */

class MemoryManager {
    constructor() {
        // 20 storage registers (R0-R19) — independent of TVM on a real 12C
        this.registers = Array(20).fill(0);
        this.financial = { n: 0, i: 0, pv: 0, pmt: 0, fv: 0 };
        // CF0 + CFj groups, each with repetition Nj (HP-12C cash-flow list)
        this.cashFlows = [];
    }

    /**
     * Store value in register
     * @param {number} registerNum - Register number (0-19)
     * @param {number} value - Value to store
     */
    store(registerNum, value) {
        if (this.isValidRegister(registerNum)) {
            this.registers[registerNum] = value;
            return true;
        }
        return false;
    }

    /**
     * Recall value from register
     * @param {number} registerNum - Register number (0-19)
     * @returns {number} Value from register
     */
    recall(registerNum) {
        if (this.isValidRegister(registerNum)) {
            return this.registers[registerNum];
        }
        return 0;
    }

    /**
     * Add value to register (STO+)
     * @param {number} registerNum - Register number
     * @param {number} value - Value to add
     */
    add(registerNum, value) {
        if (this.isValidRegister(registerNum)) {
            this.registers[registerNum] += value;
            return true;
        }
        return false;
    }

    /**
     * Subtract value from register (STO-)
     * @param {number} registerNum - Register number
     * @param {number} value - Value to subtract
     */
    subtract(registerNum, value) {
        if (this.isValidRegister(registerNum)) {
            this.registers[registerNum] -= value;
            return true;
        }
        return false;
    }

    /**
     * Multiply register by value (STO×)
     * @param {number} registerNum - Register number
     * @param {number} value - Value to multiply by
     */
    multiply(registerNum, value) {
        if (this.isValidRegister(registerNum)) {
            this.registers[registerNum] *= value;
            return true;
        }
        return false;
    }

    /**
     * Divide register by value (STO÷)
     * @param {number} registerNum - Register number
     * @param {number} value - Value to divide by
     */
    divide(registerNum, value) {
        if (this.isValidRegister(registerNum)) {
            if (value === 0) {
                return false;  // Division by zero
            }
            this.registers[registerNum] /= value;
            return true;
        }
        return false;
    }

    /**
     * Check if register number is valid
     * @param {number} registerNum - Register number to check
     * @returns {boolean} True if valid
     */
    isValidRegister(registerNum) {
        return Number.isInteger(registerNum) && registerNum >= 0 && registerNum < 20;
    }

    /**
     * Clear all registers
     */
    clear() {
        this.registers.fill(0);
    }

    /** f CLEAR Σ — statistics live in R1–R6 (Owner's Handbook §6). */
    clearSigma() {
        for (let i = 1; i <= 6; i++) this.registers[i] = 0;
    }

    /** f CLEAR REG — data + financial, program memory untouched. */
    clearReg() {
        this.registers.fill(0);
        this.clearFinancial();
    }

    /**
     * Clear financial registers (R0-R4)
     */
    clearFinancial() {
        this.financial = { n: 0, i: 0, pv: 0, pmt: 0, fv: 0 };
        this.cashFlows = [];
    }

    /**
     * Get all register values
     * @returns {Array} Array of register values
     */
    getAllRegisters() {
        return [...this.registers];
    }

    /**
     * Get financial register values
     * @returns {object} Financial register values
     */
    getFinancialRegisters() {
        return { ...this.financial };
    }

    /**
     * Set financial register value
     * @param {string} name - Register name (n, i, pv, pmt, fv)
     * @param {number} value - Value to set
     */
    setFinancialRegister(name, value) {
        const key = String(name).toLowerCase();
        if (Object.prototype.hasOwnProperty.call(this.financial, key)) {
            this.financial[key] = value;
            return true;
        }
        return false;
    }

    /**
     * Get financial register value
     * @param {string} name - Register name (n, i, pv, pmt, fv)
     * @returns {number} Register value
     */
    getFinancialRegister(name) {
        const key = String(name).toLowerCase();
        if (Object.prototype.hasOwnProperty.call(this.financial, key)) {
            return this.financial[key];
        }
        return 0;
    }

    setCF0(amount) {
        this.cashFlows = [{ amount: Number(amount) || 0, nj: 1 }];
        this.financial.n = 0;
    }

    appendCFj(amount) {
        if (this.cashFlows.length === 0) {
            this.setCF0(0);
        }
        this.cashFlows.push({ amount: Number(amount) || 0, nj: 1 });
        this.financial.n = this.cashFlows.length - 1;
    }

    setLastNj(n) {
        if (this.cashFlows.length < 2) {
            throw new Error('Error 6');
        }
        const nj = Math.max(1, Math.floor(Math.abs(Number(n) || 1)));
        this.cashFlows[this.cashFlows.length - 1].nj = nj;
    }

    /**
     * Get memory manager state
     * @returns {object} State object
     */
    getState() {
        return {
            registers: [...this.registers],
            financial: { ...this.financial },
            cashFlows: this.cashFlows.map((cf) => ({ ...cf })),
        };
    }

    /**
     * Set memory manager state
     * @param {object} state - State object
     */
    setState(state) {
        if (state.registers && Array.isArray(state.registers)) {
            this.registers = [...state.registers];
            // Ensure we have exactly 20 registers
            while (this.registers.length < 20) {
                this.registers.push(0);
            }
            this.registers = this.registers.slice(0, 20);
        }
    }

    /**
     * Reset memory to initial state
     */
    reset() {
        this.registers.fill(0);
        this.clearFinancial();
    }

    /**
     * Get register value for display purposes
     * @param {number} registerNum - Register number
     * @returns {string} Formatted register info
     */
    getRegisterInfo(registerNum) {
        if (this.isValidRegister(registerNum)) {
            return `R${registerNum}: ${this.registers[registerNum]}`;
        }
        return `Invalid register: ${registerNum}`;
    }

    /**
     * Exchange register with X (used in some operations)
     * @param {number} registerNum - Register number
     * @param {number} xValue - Current X value
     * @returns {object} {newX, success}
     */
    exchange(registerNum, xValue) {
        if (this.isValidRegister(registerNum)) {
            const temp = this.registers[registerNum];
            this.registers[registerNum] = xValue;
            return { newX: temp, success: true };
        }
        return { newX: xValue, success: false };
    }
}
