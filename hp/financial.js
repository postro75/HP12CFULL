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
    calculatePV(n, i, pmt, fv) {
        // Special case: zero interest rate
        if (Math.abs(i) < this.TOLERANCE) {
            return -(pmt * n + fv);
        }
        
        const beginFactor = this.paymentMode === 'BEGIN' ? (1 + i) : 1;
        const discount = Math.pow(1 + i, -n);
        
        return -(pmt * (1 - discount) / i * beginFactor + fv * discount);
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
        // Validation
        if (n === 0) {
            throw new Error('Error 5');  // No solution: cannot divide by zero periods
        }
        
        // Special case: zero interest rate
        if (Math.abs(i) < this.TOLERANCE) {
            return -(pv + fv) / n;
        }
        
        const beginFactor = this.paymentMode === 'BEGIN' ? (1 + i) : 1;
        const compound = Math.pow(1 + i, n);
        
        return -(pv * i + fv * i / compound) / ((1 - 1/compound) * beginFactor);
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
        // Special case: zero interest rate
        if (Math.abs(i) < this.TOLERANCE) {
            return -(pv + pmt * n);
        }
        
        const beginFactor = this.paymentMode === 'BEGIN' ? (1 + i) : 1;
        const compound = Math.pow(1 + i, n);
        
        return -(pv * compound + pmt * (compound - 1) / i * beginFactor);
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
        
        const beginFactor = this.paymentMode === 'BEGIN' ? 1 : 0;
        this.lastIterationCount = 0;
        
        for (let iteration = 0; iteration < this.MAX_ITERATIONS; iteration++) {
            this.lastIterationCount++;
            
            const compound = Math.pow(1 + i, n);
            const discount = 1 / compound;
            
            let f, df;
            
            // Special handling near i = 0 to avoid division by zero
            if (Math.abs(i) < this.TOLERANCE) {
                // Taylor series expansion around i = 0
                f = pv + pmt * n + fv;
                df = pmt * n * (n - 1) / 2 - n * fv;
            } else {
                const annuityFactor = (compound - 1) / i;
                const beginMult = 1 + i * beginFactor;
                
                // f(i) = PV + PMT × [(1+i)^n - 1]/i × (1+i×BEGIN) + FV/(1+i)^n
                f = pv + pmt * annuityFactor * beginMult + fv * discount;
                
                // Complex derivative calculation
                // df/di = PMT × BEGIN × annuityFactor + 
                //         PMT × beginMult × [n × (1+i)^(n-1) / i - annuityFactor / i] / (1+i) -
                //         n × FV × (1+i)^(-n-1)
                df = pmt * beginFactor * annuityFactor +
                     pmt * beginMult * (n * compound / i / (1 + i) - annuityFactor / i) -
                     n * fv * discount / (1 + i);
            }
            
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
        const beginFactor = this.paymentMode === 'BEGIN' ? 1 : 0;
        
        if (Math.abs(i) < this.TOLERANCE) {
            // Special case: i ≈ 0
            return pv + pmt * n * (1 + beginFactor * 0) + fv;
        }
        
        const compound = Math.pow(1 + i, n);
        const annuityFactor = (compound - 1) / i;
        const beginMult = 1 + i * beginFactor;
        
        return pv + pmt * annuityFactor * beginMult + fv / compound;
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
     * Calculate amortization for a range of periods
     * HP-12C workflow:
     *   1 [ENTER] 12 [f] [AMORT]  → Shows interest for periods 1-12
     *   [x⇄y]                      → Shows principal
     *   [RCL] [PV]                 → Shows remaining balance
     *
     * @param {MemoryManager} memory - Memory manager instance
     * @param {number} startPeriod - Starting period (1-based)
     * @param {number} endPeriod - Ending period (1-based)
     * @returns {object} {interestPaid, principalPaid, balance}
     * @throws {Error} If invalid inputs or TVM not set up
     */
    calculateAmortization(memory, startPeriod, endPeriod) {
        // Get TVM registers
        const n = memory.getFinancialRegister('n');
        const i = memory.getFinancialRegister('i') / 100;  // Convert to decimal
        const pv = memory.getFinancialRegister('pv');
        const pmt = memory.getFinancialRegister('pmt');
        
        // Validate inputs
        this.validateAmortizationInputs(n, i, pv, pmt, startPeriod, endPeriod);
        
        // Calculate amortization
        const result = this.amortizeRange(n, i, pv, pmt, startPeriod, endPeriod);
        
        // Store in state
        this.amortization.startPeriod = startPeriod;
        this.amortization.endPeriod = endPeriod;
        this.amortization.interestPaid = result.interestPaid;
        this.amortization.principalPaid = result.principalPaid;
        this.amortization.balance = result.balance;
        
        return result;
    }
    
    /**
     * Validate amortization inputs
     * @param {number} n - Total periods
     * @param {number} i - Interest rate (decimal)
     * @param {number} pv - Present value
     * @param {number} pmt - Payment amount
     * @param {number} startPeriod - Start period
     * @param {number} endPeriod - End period
     * @throws {Error} If validation fails
     */
    validateAmortizationInputs(n, i, pv, pmt, startPeriod, endPeriod) {
        // Check TVM registers are set
        if (n === null || n === 0) {
            throw new Error('Error 3');  // n not set
        }
        if (i === null) {
            throw new Error('Error 3');  // i not set
        }
        if (pv === null || pv === 0) {
            throw new Error('Error 3');  // PV not set
        }
        if (pmt === null || pmt === 0) {
            throw new Error('Error 3');  // PMT not set
        }
        
        // Validate periods
        if (!Number.isInteger(startPeriod) || startPeriod < 1) {
            throw new Error('Error 3');  // Invalid start period
        }
        if (!Number.isInteger(endPeriod) || endPeriod < startPeriod) {
            throw new Error('Error 3');  // Invalid end period
        }
        if (endPeriod > n) {
            throw new Error('Error 3');  // End period exceeds total periods
        }
        
        // Check payment is sufficient (rough check)
        // If payment doesn't cover even the first period's interest, it's negative amortization
        const firstPeriodInterest = Math.abs(pv) * Math.abs(i);
        if (Math.abs(pmt) < firstPeriodInterest * 0.01) {  // Allow very small payments for testing
            throw new Error('Error 5');  // Payment insufficient
        }
    }
    
    /**
     * Calculate amortization for a range of periods
     * Handles both END and BEGIN payment modes
     *
     * @param {number} n - Total periods
     * @param {number} i - Interest rate (decimal)
     * @param {number} pv - Present value (negative for loan)
     * @param {number} pmt - Payment amount (positive for loan repayment)
     * @param {number} startPeriod - Start period (1-based)
     * @param {number} endPeriod - End period (1-based)
     * @returns {object} {interestPaid, principalPaid, balance}
     */
    amortizeRange(n, i, pv, pmt, startPeriod, endPeriod) {
        let balance = pv;
        let totalInterest = 0;
        let totalPrincipal = 0;
        
        const isBeginMode = this.paymentMode === 'BEGIN';
        
        // Calculate period by period from 1 to endPeriod
        // We need to go from period 1 even if startPeriod > 1, to get correct balance
        for (let period = 1; period <= endPeriod; period++) {
            const periodResult = this.calculateAmortizationPeriod(balance, i, pmt, isBeginMode);
            
            // Accumulate only for periods in range
            if (period >= startPeriod && period <= endPeriod) {
                totalInterest += periodResult.interest;
                totalPrincipal += periodResult.principal;
            }
            
            // Update balance for next period
            balance = periodResult.newBalance;
        }
        
        return {
            interestPaid: totalInterest,
            principalPaid: totalPrincipal,
            balance: balance
        };
    }
    
    /**
     * Calculate amortization for a single period
     *
     * END Mode (payment at end of period):
     *   1. Interest accrues on full balance
     *   2. Payment is made
     *   3. Principal = Payment - Interest
     *   4. Balance = Balance - Principal
     *
     * BEGIN Mode (payment at beginning of period):
     *   1. Payment is made first
     *   2. Principal portion applied
     *   3. Interest accrues on reduced balance
     *   4. Balance = Balance - Principal
     *
     * @param {number} balance - Current balance
     * @param {number} i - Interest rate (decimal)
     * @param {number} pmt - Payment amount
     * @param {boolean} isBeginMode - True for BEGIN mode
     * @returns {object} {interest, principal, newBalance}
     */
    calculateAmortizationPeriod(balance, i, pmt, isBeginMode) {
        let interest, principal, newBalance;
        
        if (isBeginMode) {
            // BEGIN mode: Payment first, then interest on reduced balance
            // Calculate what principal portion of payment is
            // This is more complex - need to solve for interest and principal simultaneously
            
            // In BEGIN mode, the payment equation is:
            // payment = principal + (balance - principal) × i
            // Solving for principal:
            // principal = (payment - balance × i) / (1 - i)
            
            if (Math.abs(i) < this.TOLERANCE) {
                // Special case: zero interest
                principal = pmt;
                interest = 0;
            } else {
                // Standard BEGIN mode calculation
                principal = (pmt - balance * i) / (1 - i);
                interest = (balance - principal) * i;
            }
            
            newBalance = balance - principal;
        } else {
            // END mode: Interest first, then payment
            interest = balance * i;
            principal = pmt - interest;
            newBalance = balance - principal;
        }
        
        return {
            interest: interest,
            principal: principal,
            newBalance: newBalance
        };
    }
    
    /**
     * Get full amortization schedule (all periods)
     * Useful for detailed analysis or debugging
     *
     * @param {MemoryManager} memory - Memory manager instance
     * @returns {Array} Array of {period, payment, interest, principal, balance}
     */
    getFullAmortizationSchedule(memory) {
        const n = memory.getFinancialRegister('n');
        const i = memory.getFinancialRegister('i') / 100;
        const pv = memory.getFinancialRegister('pv');
        const pmt = memory.getFinancialRegister('pmt');
        
        // Validate
        this.validateAmortizationInputs(n, i, pv, pmt, 1, n);
        
        const schedule = [];
        let balance = pv;
        const isBeginMode = this.paymentMode === 'BEGIN';
        
        for (let period = 1; period <= n; period++) {
            const result = this.calculateAmortizationPeriod(balance, i, pmt, isBeginMode);
            
            schedule.push({
                period: period,
                payment: pmt,
                interest: result.interest,
                principal: result.principal,
                balance: result.newBalance
            });
            
            balance = result.newBalance;
        }
        
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
     * Calculate Net Present Value (future implementation)
     * @param {Array} cashFlows - Array of cash flows
     * @param {number} rate - Discount rate
     * @returns {number} NPV
     */
    calculateNPV(cashFlows, rate) {
        throw new Error('NPV not yet implemented');
    }

    /**
     * Calculate Internal Rate of Return (future implementation)
     * @param {Array} cashFlows - Array of cash flows
     * @returns {number} IRR
     */
    calculateIRR(cashFlows) {
        throw new Error('IRR not yet implemented');
    }
}
