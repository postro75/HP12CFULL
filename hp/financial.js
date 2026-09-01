/**
 * HP-12C Financial Engine
 * Implements TVM (Time Value of Money), NPV, IRR, amortization, depreciation, and date functions
 * 
 * Phase 1: Foundation - Complete class structure with TVM solvers
 * 
 * TVM Formula: PV + PMT × [(1 + i)^n - 1] / i × (1 + i × BEGIN) + FV / (1 + i)^n = 0
 * Where:
 *   n = number of periods
 *   i = periodic interest rate (decimal, e.g., 0.005 for 0.5%)
 *   PV = present value (negative = outflow, positive = inflow)
 *   PMT = payment per period (negative = outflow, positive = inflow)
 *   FV = future value (negative = outflow, positive = inflow)
 *   BEGIN = 0 for END mode, 1 for BEGIN mode
 */

class FinancialEngine {
    constructor() {
        // Payment timing mode
        this.paymentMode = 'END';  // 'BEGIN' or 'END'
        // C indicator: compound (true) vs simple (false) interest on odd first period
        this.compoundOdd = false;
        
        // Newton-Raphson configuration
        this.MAX_ITERATIONS = 200;
        this.TOLERANCE = 1e-10;
        this.MIN_RATE = -0.99999;  // Prevent division by zero
        this.MAX_RATE = 1000.0;    // Prevent overflow
        
        // Calculation state tracking
        this.lastSolvedVariable = null;
        this.lastIterationCount = 0;
        
        // Amortization state
        this.amortization = {
            startPeriod: null,
            endPeriod: null,
            interestPaid: null,
            principalPaid: null,
            balance: null,
            schedule: []  // Full period-by-period schedule
        };
    }

    // ============================================
    // PUBLIC API - TVM SOLVERS
    // ============================================
    
    /**
     * Solve for n (number of periods)
     * Uses Newton-Raphson iteration for general case, closed-form for single cash flow
     * 
     * @param {MemoryManager} memory - Memory manager instance
     * @returns {number} Calculated n value
     * @throws {Error} If solution doesn't exist or invalid inputs
     */
    solveN(memory) {
        const i = memory.getFinancialRegister('i') / 100;  // Convert percentage to decimal
        const pv = memory.getFinancialRegister('pv');
        const pmt = memory.getFinancialRegister('pmt');
        const fv = memory.getFinancialRegister('fv');
        
        // Validation
        this.validateTVMInputs(i, pv, pmt, fv);
        
        // Special case: single cash flow (PMT = 0)
        if (Math.abs(pmt) < this.TOLERANCE) {
            return this.solveNSingleCashFlow(i, pv, fv);
        }
        
        // General case: Newton-Raphson iteration
        const result = this.solveNIterative(i, pv, pmt, fv);
        this.lastSolvedVariable = 'n';
        return result;
    }

    /**
     * Solve for i (interest rate)
     * Uses Newton-Raphson iteration with intelligent initial guess and bisection fallback
     * This is the most complex TVM calculation
     * 
     * @param {MemoryManager} memory - Memory manager instance
     * @returns {number} Calculated i value (as percentage, e.g., 6.0 for 6%)
     * @throws {Error} If solution doesn't exist or invalid inputs
     */
    solveI(memory) {
        const n = memory.getFinancialRegister('n');
        const pv = memory.getFinancialRegister('pv');
        const pmt = memory.getFinancialRegister('pmt');
        const fv = memory.getFinancialRegister('fv');
        
        // Validation
        this.validateTVMInputs(n, pv, pmt, fv);
        
        // Newton-Raphson iteration with intelligent initial guess
        const result = this.solveIIterative(n, pv, pmt, fv) * 100;  // Convert to percentage
        this.lastSolvedVariable = 'i';
        return result;
    }

    /**
     * Solve for PV (present value)
     * Uses closed-form formula with special case for i = 0
     * 
     * @param {MemoryManager} memory - Memory manager instance
     * @returns {number} Calculated PV value
     */
    solvePV(memory) {
        const n = memory.getFinancialRegister('n');
        const i = memory.getFinancialRegister('i') / 100;  // Convert percentage to decimal
        const pmt = memory.getFinancialRegister('pmt');
        const fv = memory.getFinancialRegister('fv');
        
        const result = this.calculatePV(n, i, pmt, fv);
        this.lastSolvedVariable = 'pv';
        return result;
    }

    /**
     * Solve for PMT (payment)
     * Uses closed-form formula with special case for i = 0
     * 
     * @param {MemoryManager} memory - Memory manager instance
     * @returns {number} Calculated PMT value
     */
    solvePMT(memory) {
        const n = memory.getFinancialRegister('n');
        const i = memory.getFinancialRegister('i') / 100;  // Convert percentage to decimal
        const pv = memory.getFinancialRegister('pv');
        const fv = memory.getFinancialRegister('fv');
        
        const result = this.calculatePMT(n, i, pv, fv);
        this.lastSolvedVariable = 'pmt';
        return result;
    }

    /**
     * Solve for FV (future value)
     * Uses closed-form formula with special case for i = 0
     * 
     * @param {MemoryManager} memory - Memory manager instance
     * @returns {number} Calculated FV value
     */
    solveFV(memory) {
        const n = memory.getFinancialRegister('n');
        const i = memory.getFinancialRegister('i') / 100;  // Convert percentage to decimal
        const pv = memory.getFinancialRegister('pv');
        const pmt = memory.getFinancialRegister('pmt');
        
        const result = this.calculateFV(n, i, pv, pmt);
        this.lastSolvedVariable = 'fv';
        return result;
    }

    // ============================================
    // CLOSED-FORM CALCULATORS
    // ============================================
    
    /**
     * Calculate PV using closed-form formula
     * Formula: PV = -PMT × [(1 - (1 + i)^-n) / i] × (1 + i × BEGIN) - FV / (1 + i)^n
     * Special case when i = 0: PV = -(PMT × n + FV)
     * 
     * @param {number} n - Number of periods
     * @param {number} i - Periodic interest rate (decimal)
     * @param {number} pmt - Payment per period
     * @param {number} fv - Future value
     * @returns {number} Present value
     */
    splitN(n) {
        const an = Math.abs(Number(n) || 0);
        let nInt = Math.floor(an + 1e-12);
        let frac = an - nInt;
        if (frac < 1e-10) frac = 0;
        if (frac > 1 - 1e-10) { nInt += 1; frac = 0; }
        return { nInt: nInt, frac: frac };
    }

    oddFactor(i, frac) {
        if (frac === 0 || Math.abs(i) < this.TOLERANCE) return 1;
        if (this.compoundOdd) return Math.pow(1 + i, frac);
        return 1 + i * frac;
    }

    calculatePV(n, i, pmt, fv) {
        const parts = this.splitN(n);
        const nInt = parts.nInt;
        const odd = this.oddFactor(i, parts.frac);
        if (Math.abs(i) < this.TOLERANCE) {
            return -(pmt * n + fv);
        }
        const beginFactor = this.paymentMode === 'BEGIN' ? (1 + i) : 1;
        const discount = Math.pow(1 + i, -nInt);
        return -(pmt * (1 - discount) / i * beginFactor + fv * discount) / odd;
    }

    /**
     * Calculate PMT using closed-form formula
     * Formula: PMT = -(PV + FV / (1 + i)^n) × i / [(1 - (1 + i)^-n) × (1 + i × BEGIN)]
     * Special case when i = 0: PMT = -(PV + FV) / n
     * 
     * @param {number} n - Number of periods
     * @param {number} i - Periodic interest rate (decimal)
     * @param {number} pv - Present value
     * @param {number} fv - Future value
     * @returns {number} Payment per period
     */
    calculatePMT(n, i, pv, fv) {
        const parts = this.splitN(n);
        const nInt = parts.nInt;
        const odd = this.oddFactor(i, parts.frac);
        if (nInt === 0) {
            throw new Error('Error 5');
        }
        if (Math.abs(i) < this.TOLERANCE) {
            return -(pv + fv) / n;
        }
        const beginFactor = this.paymentMode === 'BEGIN' ? (1 + i) : 1;
        const compound = Math.pow(1 + i, nInt);
        return -(pv * odd * i + fv * i / compound) / ((1 - 1 / compound) * beginFactor);
    }

    /**
     * Calculate FV using closed-form formula
     * Formula: FV = -PV × (1 + i)^n - PMT × [(1 + i)^n - 1] / i × (1 + i × BEGIN)
     * Special case when i = 0: FV = -(PV + PMT × n)
     * 
     * @param {number} n - Number of periods
     * @param {number} i - Periodic interest rate (decimal)
     * @param {number} pv - Present value
     * @param {number} pmt - Payment per period
     * @returns {number} Future value
     */
    calculateFV(n, i, pv, pmt) {
        const parts = this.splitN(n);
        const nInt = parts.nInt;
        const odd = this.oddFactor(i, parts.frac);
        if (Math.abs(i) < this.TOLERANCE) {
            return -(pv + pmt * n);
        }
        const beginFactor = this.paymentMode === 'BEGIN' ? (1 + i) : 1;
        const compound = Math.pow(1 + i, nInt);
        return -(pv * odd * compound + pmt * (compound - 1) / i * beginFactor);
    }

    // ============================================
    // NEWTON-RAPHSON ITERATIVE SOLVERS
    // ============================================
    
    /**
     * Solve for n when PMT = 0 (single cash flow)
     * Direct logarithmic formula: n = ln(FV / -PV) / ln(1 + i)
     * 
     * @param {number} i - Periodic interest rate (decimal)
     * @param {number} pv - Present value
     * @param {number} fv - Future value
     * @returns {number} Number of periods
     * @throws {Error} If no solution exists
     */
    solveNSingleCashFlow(i, pv, fv) {
        // Check for valid cash flow signs
        if (pv === 0 || fv === 0 || pv * fv > 0) {
            throw new Error('Error 5');  // No solution: need opposite signs for PV and FV
        }
        
        if (Math.abs(i) < this.TOLERANCE) {
            throw new Error('Error 5');  // Cannot solve with i=0 and PMT=0
        }
        
        return Math.log(-fv / pv) / Math.log(1 + i);
    }

    /**
     * Solve for n using Newton-Raphson iteration
     * Function: f(n) = PV × (1+i)^n + PMT × [(1+i)^n - 1]/i × (1+i×BEGIN) + FV
     * Derivative: f'(n) = PV × (1+i)^n × ln(1+i) + PMT × [(1+i)^n × ln(1+i)]/i × (1+i×BEGIN)
     * 
     * @param {number} i - Periodic interest rate (decimal)
     * @param {number} pv - Present value
     * @param {number} pmt - Payment per period
     * @param {number} fv - Future value
     * @returns {number} Number of periods
     * @throws {Error} If no convergence or no solution
     */
    solveNIterative(i, pv, pmt, fv) {
        // Initial guess: use approximate formula
        let n = 10.0;  // Start with 10 periods as reasonable default
        
        const beginFactor = this.paymentMode === 'BEGIN' ? (1 + i) : 1;
        this.lastIterationCount = 0;
        
        for (let iteration = 0; iteration < this.MAX_ITERATIONS; iteration++) {
            this.lastIterationCount++;
            
            const compound = Math.pow(1 + i, n);
            const lnCompound = Math.log(1 + i);
            
            // f(n) = PV × (1+i)^n + PMT × [(1+i)^n - 1]/i × (1+i×BEGIN) + FV
            const f = pv * compound + 
                     pmt * (compound - 1) / i * beginFactor + 
                     fv;
            
            // f'(n) = derivative with respect to n
            const df = pv * compound * lnCompound +
                      pmt * compound * lnCompound / i * beginFactor;
            
            if (Math.abs(df) < this.TOLERANCE) {
                throw new Error('Error 7');  // No solution (derivative too small)
            }
            
            // Newton-Raphson step
            const nNew = n - f / df;
            
            // Check convergence
            if (Math.abs(nNew - n) < this.TOLERANCE && Math.abs(f) < this.TOLERANCE) {
                return nNew;
            }
            
            // Check for valid range
            if (nNew < 0 || nNew > 99999) {
                throw new Error('Error 5');  // Out of range
            }
            
            n = nNew;
        }
        
        throw new Error('Error 8');  // No convergence after max iterations
    }

    /**
     * Solve for i using Newton-Raphson iteration
     * Function: f(i) = PV + PMT × [(1+i)^n - 1]/i × (1+i×BEGIN) + FV/(1+i)^n
     * Derivative: Complex - see implementation
     * 
     * @param {number} n - Number of periods
     * @param {number} pv - Present value
     * @param {number} pmt - Payment per period
     * @param {number} fv - Future value
     * @returns {number} Periodic interest rate (decimal)
     * @throws {Error} If no convergence
     */
    solveIIterative(n, pv, pmt, fv) {
        // Initial guess using heuristic
        let i = this.getInitialGuessForI(n, pv, pmt, fv);
        
        this.lastIterationCount = 0;
        
        for (let iteration = 0; iteration < this.MAX_ITERATIONS; iteration++) {
            this.lastIterationCount++;
            const f = this.evaluateTVM(n, i, pv, pmt, fv);
            const h = Math.max(1e-8, Math.abs(i) * 1e-6);
            const df = (this.evaluateTVM(n, i + h, pv, pmt, fv) -
                        this.evaluateTVM(n, i - h, pv, pmt, fv)) / (2 * h);
            
            if (Math.abs(df) < this.TOLERANCE) {
                // Derivative too small, try bisection method as fallback
                return this.solveIBisection(n, pv, pmt, fv);
            }
            
            // Newton-Raphson step
            const iNew = i - f / df;
            
            // Check convergence
            if (Math.abs(iNew - i) < this.TOLERANCE && Math.abs(f) < this.TOLERANCE) {
                return iNew;
            }
            
            // Bounds checking
            if (iNew < this.MIN_RATE || iNew > this.MAX_RATE) {
                // Out of reasonable bounds, use bisection
                return this.solveIBisection(n, pv, pmt, fv);
            }
            
            i = iNew;
        }
        
        throw new Error('Error 8');  // No convergence after max iterations
    }

    /**
     * Get intelligent initial guess for interest rate
     * Uses simple heuristic based on cash flows
     * 
     * @param {number} n - Number of periods
     * @param {number} pv - Present value
     * @param {number} pmt - Payment per period
     * @param {number} fv - Future value
     * @returns {number} Initial guess for i (decimal)
     */
    getInitialGuessForI(n, pv, pmt, fv) {
        // Check for trivial cases
        if (Math.abs(pv) < this.TOLERANCE && Math.abs(pmt) < this.TOLERANCE) {
            return 0.1;  // Default 10% if no meaningful input
        }
        
        // Simple approximation based on total cash flow
        const totalPayments = pmt * n;
        const netCashFlow = fv - pv - totalPayments;
        const avgBalance = (Math.abs(pv) + Math.abs(fv)) / 2;
        
        if (avgBalance < this.TOLERANCE) {
            return 0.1;  // Default 10%
        }
        
        // Rough estimate: return / (time × average balance)
        const estimate = netCashFlow / (n * avgBalance);
        
        // Clamp to reasonable range
        return Math.max(this.MIN_RATE, Math.min(this.MAX_RATE, estimate));
    }

    /**
     * Solve for i using bisection method (fallback when Newton-Raphson fails)
     * Guaranteed to converge but slower than Newton-Raphson
     * 
     * @param {number} n - Number of periods
     * @param {number} pv - Present value
     * @param {number} pmt - Payment per period
     * @param {number} fv - Future value
     * @returns {number} Periodic interest rate (decimal)
     * @throws {Error} If no convergence
     */
    solveIBisection(n, pv, pmt, fv) {
        let iLow = -0.99;   // Lower bound
        let iHigh = 10.0;   // Upper bound (1000%)
        
        const beginFactor = this.paymentMode === 'BEGIN' ? 1 : 0;
        
        for (let iteration = 0; iteration < this.MAX_ITERATIONS; iteration++) {
            const iMid = (iLow + iHigh) / 2;
            
            // Evaluate f at midpoint
            const f = this.evaluateTVM(n, iMid, pv, pmt, fv);
            
            if (Math.abs(f) < this.TOLERANCE) {
                return iMid;
            }
            
            // Narrow the interval
            const fLow = this.evaluateTVM(n, iLow, pv, pmt, fv);
            if (f * fLow < 0) {
                iHigh = iMid;
            } else {
                iLow = iMid;
            }
            
            if (Math.abs(iHigh - iLow) < this.TOLERANCE) {
                return iMid;
            }
        }
        
        throw new Error('Error 8');  // No convergence
    }

    /**
     * Evaluate TVM equation at given interest rate
     * Used by bisection method
     * 
     * @param {number} n - Number of periods
     * @param {number} i - Interest rate to evaluate
     * @param {number} pv - Present value
     * @param {number} pmt - Payment per period
     * @param {number} fv - Future value
     * @returns {number} TVM equation result
     */
    evaluateTVM(n, i, pv, pmt, fv) {
        const parts = this.splitN(n);
        const nInt = parts.nInt;
        const odd = this.oddFactor(i, parts.frac);
        const beginFactor = this.paymentMode === 'BEGIN' ? 1 : 0;
        if (Math.abs(i) < this.TOLERANCE) {
            return pv + pmt * n + fv;
        }
        const compound = Math.pow(1 + i, nInt);
        const annuityFactor = (compound - 1) / i;
        const beginMult = 1 + i * beginFactor;
        return pv * odd + pmt * annuityFactor * beginMult + fv / compound;
    }

    // ============================================
    // VALIDATION & HELPERS
    // ============================================
    
    /**
     * Validate TVM input values
     * Checks for NaN, Infinity, and other invalid inputs
     * 
     * @param {...number} values - Values to validate
     * @throws {Error} If any value is invalid
     */
    validateTVMInputs(...values) {
        for (const val of values) {
            if (!isFinite(val)) {
                throw new Error('Error 0');  // Invalid input
            }
        }
    }

    // ============================================
    // PAYMENT MODE MANAGEMENT
    // ============================================
    
    /**
     * Set payment timing mode
     * BEGIN: payments at start of period (annuity due)
     * END: payments at end of period (ordinary annuity)
     * 
     * @param {string} mode - 'BEGIN' or 'END'
     * @throws {Error} If mode is invalid
     */
    setPaymentMode(mode) {
        if (mode !== 'BEGIN' && mode !== 'END') {
            throw new Error('Invalid payment mode: must be BEGIN or END');
        }
        this.paymentMode = mode;
    }

    /**
     * Get current payment timing mode
     * @returns {string} 'BEGIN' or 'END'
     */
    getPaymentMode() {
        return this.paymentMode;
    }

    /**
     * Toggle between BEGIN and END modes
     * @returns {string} New payment mode
     */
    togglePaymentMode() {
        this.paymentMode = this.paymentMode === 'BEGIN' ? 'END' : 'BEGIN';
        return this.paymentMode;
    }

    /**
     * Check if in BEGIN mode
     * @returns {boolean} True if BEGIN mode
     */
    isBeginMode() {
        return this.paymentMode === 'BEGIN';
    }

    // ============================================
    // STATE & DIAGNOSTICS
    // ============================================
    
    /**
     * Get last solved variable
     * @returns {string|null} Last variable that was solved (n, i, pv, pmt, fv)
     */
    getLastSolvedVariable() {
        return this.lastSolvedVariable;
    }

    /**
     * Get iteration count from last iterative solve
     * Useful for performance monitoring
     * @returns {number} Number of iterations
     */
    getLastIterationCount() {
        return this.lastIterationCount;
    }

    /**
     * Reset financial engine state
     */
    reset() {
        this.paymentMode = 'END';
        this.compoundOdd = false;
        this.lastSolvedVariable = null;
        this.lastIterationCount = 0;
        this.amortization = {
            startPeriod: null,
            endPeriod: null,
            interestPaid: null,
            principalPaid: null,
            balance: null,
            schedule: []
        };
    }

    // ============================================
    // AMORTIZATION ENGINE
    // ============================================

    /**
     * Amortize the next `periods` payments (Owner's Handbook §3).
     * Keystrokes: 12 [f] [AMORT] → interest in X; [x⇄y] principal; [RCL] [PV] balance.
     * n accumulates amortized count; PV becomes remaining balance.
     *
     * @param {MemoryManager} memory
     * @param {number} periods - periods to amortize (from X)
     * @param {number} precision - display decimals for per-period INT rounding
     * @returns {{interestPaid, principalPaid, balance, periodsJust, n}}
     */
    calculateAmortization(memory, periods, precision = 2) {
        const iPct = memory.getFinancialRegister('i');
        const pv = memory.getFinancialRegister('pv');
        const pmt = memory.getFinancialRegister('pmt');
        let n = memory.getFinancialRegister('n') || 0;
        const count = Math.floor(Math.abs(Number(periods)));

        if (!Number.isFinite(count) || count < 1) throw new Error('Error 3');
        if (iPct === null || iPct === undefined) throw new Error('Error 3');
        if (pv === null || pv === undefined) throw new Error('Error 3');
        if (pmt === null || pmt === undefined || pmt === 0) throw new Error('Error 3');

        const result = this.amortizeNext(n, iPct, pv, pmt, count, precision);
        this.amortization.startPeriod = n + 1;
        this.amortization.endPeriod = n + count;
        this.amortization.interestPaid = result.interestPaid;
        this.amortization.principalPaid = result.principalPaid;
        this.amortization.balance = result.balance;
        return result;
    }

    /**
     * Handbook cash-flow AMORT (finanx / HP-12C):
     * INT = ±round(|PV×i/100|, FIX); PRN = PMT − INT; PV ← PV + PRN; n ← n + x
     */
    amortizeNext(n, iPct, pv, pmt, periods, precision) {
        const factor = Math.pow(10, precision);
        const begin = this.paymentMode === 'BEGIN';
        let sumINT = 0;
        let sumPRN = 0;
        let balance = pv;

        for (let j = 0; j < periods; j++) {
            let INT;
            if (j === 0 && begin) {
                INT = 0;
            } else {
                INT = Math.abs(balance * iPct / 100);
                INT = Math.round(INT * factor) / factor;
                if (pmt < 0) INT = -INT;
            }
            sumINT += INT;
            const PRN = pmt - INT;
            sumPRN += PRN;
            balance = balance + PRN;
        }

        return {
            interestPaid: sumINT,
            principalPaid: sumPRN,
            balance,
            periodsJust: periods,
            n: n + periods
        };
    }

    /** Single-period helper using handbook cash-flow signs. */
    calculateAmortizationPeriod(balance, i, pmt, isBeginMode) {
        let interest;
        if (isBeginMode) {
            interest = 0;
        } else {
            interest = Math.abs(balance * i);
            if (pmt < 0) interest = -interest;
        }
        const principal = pmt - interest;
        return {
            interest,
            principal,
            newBalance: balance + principal
        };
    }

    getFullAmortizationSchedule(memory, precision = 2) {
        const iPct = memory.getFinancialRegister('i');
        const pv = memory.getFinancialRegister('pv');
        const pmt = memory.getFinancialRegister('pmt');
        const total = Math.floor(Math.abs(memory.getFinancialRegister('n') || 0));
        if (total < 1) throw new Error('Error 3');
        if (pmt === null || pmt === 0) throw new Error('Error 3');

        const schedule = [];
        let balance = pv;
        const begin = this.paymentMode === 'BEGIN';
        const factor = Math.pow(10, precision);
        for (let j = 0; j < total; j++) {
            let INT;
            if (j === 0 && begin) INT = 0;
            else {
                INT = Math.abs(balance * iPct / 100);
                INT = Math.round(INT * factor) / factor;
                if (pmt < 0) INT = -INT;
            }
            const PRN = pmt - INT;
            balance = balance + PRN;
            schedule.push({
                period: j + 1,
                payment: pmt,
                interest: INT,
                principal: PRN,
                balance
            });
        }
        this.amortization.schedule = schedule;
        return schedule;
    }

    /**
     * Get last amortization results
     * @returns {object} Last amortization calculation results
     */
    getAmortizationResults() {
        return {
            startPeriod: this.amortization.startPeriod,
            endPeriod: this.amortization.endPeriod,
            interestPaid: this.amortization.interestPaid,
            principalPaid: this.amortization.principalPaid,
            balance: this.amortization.balance
        };
    }
    
    /**
     * Get interest paid from last amortization
     * @returns {number} Interest paid
     */
    getAmortInterest() {
        return this.amortization.interestPaid;
    }
    
    /**
     * Get principal paid from last amortization
     * @returns {number} Principal paid
     */
    getAmortPrincipal() {
        return this.amortization.principalPaid;
    }
    
    /**
     * Get remaining balance from last amortization
     * @returns {number} Remaining balance
     */
    getAmortBalance() {
        return this.amortization.balance;
    }

    /**
     * NPV of memory.cashFlows at memory.financial.i (% per period).
     * CF0 at period 0; each later CFj is repeated Nj times.
     */
    calculateNPV(memory) {
        const flows = memory.cashFlows || [];
        if (!flows.length) {
            throw new Error('Error 3');
        }
        const i = memory.getFinancialRegister('i') / 100;
        const npv = this._sumPV(flows, i);
        if (!isFinite(npv)) {
            throw new Error('Error 3');
        }
        return npv;
    }

    _sumPV(flows, i) {
        const v = 1 + i;
        if (v <= 0) return NaN;
        let total = flows[0].amount;
        let period = 0;
        for (let j = 1; j < flows.length; j++) {
            const reps = Math.max(1, flows[j].nj || 1);
            for (let k = 0; k < reps; k++) {
                period += 1;
                total += flows[j].amount / Math.pow(v, period);
            }
        }
        return total;
    }

    /**
     * IRR as percent per period (same units as i).
     */
    calculateIRR(memory) {
        const flows = memory.cashFlows || [];
        if (flows.length < 2) {
            throw new Error('Error 3');
        }
        let hasPos = false;
        let hasNeg = false;
        for (const cf of flows) {
            if (cf.amount > 0) hasPos = true;
            if (cf.amount < 0) hasNeg = true;
        }
        if (!(hasPos && hasNeg)) {
            throw new Error('Error 3');
        }

        const lo0 = -0.99;
        const hi0 = 10;
        let fLo = this._sumPV(flows, lo0);
        if (!isFinite(fLo)) {
            throw new Error('Error 3');
        }
        let lo = lo0;
        let hi = hi0;
        let bracketed = false;
        let a = lo0;
        let fa = fLo;
        for (let k = 1; k <= 50; k++) {
            const t = lo0 + (hi0 - lo0) * k / 50;
            const ft = this._sumPV(flows, t);
            if (!isFinite(ft)) continue;
            if (fa * ft < 0) {
                lo = a;
                hi = t;
                fLo = fa;
                bracketed = true;
                break;
            }
            a = t;
            fa = ft;
        }
        if (!bracketed) {
            throw new Error('Error 3');
        }

        for (let k = 0; k < this.MAX_ITERATIONS; k++) {
            const mid = 0.5 * (lo + hi);
            const fm = this._sumPV(flows, mid);
            if (!isFinite(fm)) {
                throw new Error('Error 3');
            }
            if (Math.abs(fm) < this.TOLERANCE || (hi - lo) < this.TOLERANCE) {
                return mid * 100;
            }
            if (fm * fLo < 0) {
                hi = mid;
            } else {
                lo = mid;
                fLo = fm;
            }
        }
        return 0.5 * (lo + hi) * 100;
    }
}
