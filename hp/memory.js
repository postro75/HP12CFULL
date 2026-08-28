/**
 * HP-12C Memory Manager
 * Manages 20 storage registers (R0-R19)
 */

class MemoryManager {
    constructor() {
        // 20 storage registers (R0-R19)
        this.registers = Array(20).fill(0);
        
        // Financial registers are mapped to regular registers
        // R0 = n, R1 = i, R2 = PV, R3 = PMT, R4 = FV
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

    /**
     * Clear financial registers (R0-R4)
     */
    clearFinancial() {
        for (let i = 0; i < 5; i++) {
            this.registers[i] = 0;
        }
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
        return {
            n: this.registers[0],
            i: this.registers[1],
            pv: this.registers[2],
            pmt: this.registers[3],
            fv: this.registers[4]
        };
    }

    /**
     * Set financial register value
     * @param {string} name - Register name (n, i, pv, pmt, fv)
     * @param {number} value - Value to set
     */
    setFinancialRegister(name, value) {
        const mapping = {
            'n': 0,
            'i': 1,
            'pv': 2,
            'pmt': 3,
            'fv': 4
        };
        
        const registerNum = mapping[name.toLowerCase()];
        if (registerNum !== undefined) {
            this.registers[registerNum] = value;
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
        const mapping = {
            'n': 0,
            'i': 1,
            'pv': 2,
            'pmt': 3,
            'fv': 4
        };
        
        const registerNum = mapping[name.toLowerCase()];
        if (registerNum !== undefined) {
            return this.registers[registerNum];
        }
        return 0;
    }

    /**
     * Get memory manager state
     * @returns {object} State object
     */
    getState() {
        return {
            registers: [...this.registers]
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
