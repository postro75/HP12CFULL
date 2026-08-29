/**
 * HP-12C Calculator Controller
 * Main controller coordinating all calculator components
 */

class Calculator {
    constructor() {
        this.stack = new RPNStack();
        this.display = new DisplayManager();
        this.memory = new MemoryManager();
        this.financial = new FinancialEngine();
        this.math = new MathEngine();
        
        // Input state
        this.currentInput = '';
        this.isNewNumber = true;
        this.hasDecimal = false;
        this.isExponent = false;
        
        // Prefix state
        this.prefixF = false;
        this.prefixG = false;
        
        // Pending operation state (for STO, RCL requiring register number)
        this.pendingOperation = null;

        // HP-12C: TVM keys store X after a new entry/result, otherwise solve.
        this.tvmStoreNext = false;
        this.dmyMode = false;
        this.eexActive = false;
        this.eexMantissa = 0;
        this.eexDigits = '';
        this.eexNeg = false;
        this.prgmMode = false;
        this.program = [];
        this.pc = 0;
        this.skipNext = false;
        this.pendingGto = false;
        this.gtoDigits = '';
        this.running = false;
        
        // References to DOM elements
        this.displayElement = null;
        this.buttons = [];
    }

    /**
     * Initialize calculator with DOM elements
     */
    initialize() {
        // Get display element
        this.displayElement = document.getElementById('displayValue');
        
        // Get indicator elements
        const indicators = {
            f: document.getElementById('indF'),
            g: document.getElementById('indG'),
            user: document.getElementById('indUser'),
            begin: document.getElementById('indBegin'),
            c: document.getElementById('indC'),
            running: document.getElementById('indRunning')
        };
        
        // Initialize display
        this.display.initialize(this.displayElement, indicators);
        
        // Attach button event listeners
        this.attachEventListeners();
        
        // Initial display
        this.updateDisplay();
        
        console.log('HP-12C Calculator initialized');
    }

    /**
     * Attach event listeners to all buttons
     */
    attachEventListeners() {
        this.buttons = document.querySelectorAll('.key');
        
        this.buttons.forEach(button => {
            button.addEventListener('click', (e) => {
                this.handleButtonClick(button);
                
                // Visual feedback
                button.classList.add('pressed');
                setTimeout(() => button.classList.remove('pressed'), 150);
            });
        });
    }

    /**
     * Handle button click
     * @param {HTMLElement} button - Button element
     */
    handleButtonClick(button) {
        const key = button.dataset.key;
        const primary = button.dataset.primary;

        if (this.pendingGto && key.startsWith('digit-')) {
            this.gtoDigits += key.replace('digit-', '');
            if (this.gtoDigits.length >= 2) {
                const line = parseInt(this.gtoDigits, 10);
                this.pendingGto = false;
                this.gtoDigits = '';
                if (this.prgmMode) {
                    if (this.program.length) {
                        this.program[this.program.length - 1].addr = line;
                    }
                } else {
                    this.pc = Math.max(0, Math.min(line - 1, this.program.length));
                }
            }
            this.updateDisplay();
            return;
        }

        if (this.prgmMode && key !== 'prefix-f' && key !== 'prefix-g' && key !== 'on') {
            if (this.prefixF && key === 'run-stop') {
                this.prgmMode = false;
                this.prefixF = false;
                this.display.setIndicator('f', false);
                this.updateDisplay();
                return;
            }
            if (this.prefixG && key === 'roll-down') {
                this.pendingGto = true;
                this.gtoDigits = '';
                this.recordStep(key);
                this.prefixG = false;
                this.display.setIndicator('g', false);
                this.updateDisplay();
                return;
            }
            if (key === 'sst') {
                if (this.prefixG) {
                    this.pc = Math.max(0, this.pc - 1);
                    this.prefixG = false;
                } else {
                    this.pc = Math.min(this.program.length, this.pc + 1);
                }
                this.updateDisplay();
                return;
            }
            this.recordStep(key);
            this.prefixF = false;
            this.prefixG = false;
            this.display.setIndicator('f', false);
            this.display.setIndicator('g', false);
            this.updateDisplay();
            return;
        }
        
        if (this.prefixF) {
            this.handleGoldFunction(key);
            this.prefixF = false;
            this.display.setIndicator('f', false);
        } else if (this.prefixG) {
            this.handleBlueFunction(key);
            this.prefixG = false;
            this.display.setIndicator('g', false);
        } else {
            this.handlePrimaryFunction(key, primary);
        }
        
        this.updateDisplay();
    }

    /**
     * Handle primary function (no prefix)
     * @param {string} key - Button key
     * @param {string} primary - Primary label
     */
    handlePrimaryFunction(key, primary) {
        if (this.consumePendingMemory(key)) {
            return;
        }

        // Number keys (digit-0 through digit-9)
        if (key.startsWith('digit-')) {
            const digit = key.replace('digit-', '');
            this.enterDigit(digit);
            return;
        }
        
        // Decimal point
        if (key === 'decimal') {
            this.enterDecimal();
            return;
        }
        
        switch(key) {
            case 'prefix-f':
                this.prefixF = true;
                this.display.setIndicator('f', true);
                break;
                
            case 'prefix-g':
                this.prefixG = true;
                this.display.setIndicator('g', true);
                break;
                
            case 'enter':
                this.enter();
                break;
                
            case 'clx':
                this.clearX();
                break;
                
            case 'roll-down':
                this.rollDown();
                break;
                
            case 'swap-xy':
                this.swapXY();
                break;
                
            case 'chs':
                this.changeSign();
                break;
                
            case 'op-add':
                this.add();
                break;
                
            case 'op-subtract':
                this.subtract();
                break;
                
            case 'op-multiply':
                this.multiply();
                break;
                
            case 'op-divide':
                this.divide();
                break;
                
            case 'sto':
                // STO requires a following digit - enter pending state
                this.pendingOperation = 'sto';
                console.log('STO: Waiting for register number...');
                break;
                
            case 'rcl':
                // RCL requires a following digit - enter pending state
                this.pendingOperation = 'rcl';
                console.log('RCL: Waiting for register number...');
                break;
                
            case 'on':
                this.reset();
                break;
            
            // Math functions
            case 'reciprocal':
                this.reciprocal();
                break;
                
            case 'percent':
                this.percent();
                break;
                
            case 'percent-total':
                this.percentTotal();
                break;
                
            case 'delta-percent':
                this.deltaPercent();
                break;
                
            case 'power-yx':
                this.power();
                break;
            
            // Financial TVM keys
            case 'n':
                this.handleTVMKey('n');
                break;
                
            case 'i':
                this.handleTVMKey('i');
                break;
                
            case 'pv':
                this.handleTVMKey('pv');
                break;
                
            case 'pmt':
                this.handleTVMKey('pmt');
                break;
                
            case 'fv':
                this.handleTVMKey('fv');
                break;

            case 'eex':
                this.handleEex();
                break;

            case 'sum-plus':
                this.handleSigmaPlus();
                break;

            case 'run-stop':
                this.runProgram();
                break;

            case 'sst':
                this.sstRun();
                break;
                
            default:
                console.log('Unimplemented function:', key);
        }
    }

    /**
     * Handle gold function (f prefix)
     * @param {string} key - Button key
     */
    handleGoldFunction(key) {
        console.log('Gold function:', key);

        if (key.startsWith('digit-')) {
            const n = parseInt(key.replace('digit-', ''), 10);
            this.display.setFormat('fixed', n);
            this.updateDisplay();
            return;
        }
        
        switch(key) {
            case 'n':  // f n = AMORT
                this.handleAmortization();
                break;
            case 'pv':  // f PV = NPV
                this.handleNPV();
                break;
            case 'fv':  // f FV = IRR
                this.handleIRR();
                break;
            case 'pmt':  // f PMT = RND
                this.handleRound();
                break;
            case 'i':  // f i = INT simple interest
                this.handleSimpleInterest();
                break;
            case 'chs':  // f CHS = DATE
                this.handleDateAdd();
                break;
            case 'power-yx':  // f y^x = PRICE
                this.handleBondPrice();
                break;
            case 'reciprocal':  // f 1/x = YTM
                this.handleBondYtm();
                break;
            case 'percent-total':  // f %T = SL
                this.handleDepr('sl');
                break;
            case 'delta-percent':  // f Δ% = SOYD
                this.handleDepr('soyd');
                break;
            case 'percent':  // f % = DB
                this.handleDepr('db');
                break;
            case 'clx':  // f CLx = CLEAR FIN
                this.memory.clearFinancial();
                break;
            case 'run-stop':  // f R/S = P/R
                this.prgmMode = true;
                this.pc = this.program.length;
                break;
            default:
                console.log('Unimplemented gold function:', key);
        }
    }

    /**
     * Handle blue function (g prefix)
     * @param {string} key - Button key
     */
    handleBlueFunction(key) {
        console.log('Blue function:', key);
        
        switch(key) {
            case 'power-yx':  // g yˣ = √x (square root)
                this.squareRoot();
                break;
                
            case 'reciprocal':  // g 1/x = eˣ (exponential)
                this.exponential();
                break;
                
            case 'percent-total':  // g %T = LN (natural log)
                this.naturalLog();
                break;
                
            case 'delta-percent':  // g Δ% = FRAC (fractional part)
                this.fractionalPart();
                break;
                
            case 'percent':  // g % = INTG (integer part)
                this.integerPart();
                break;
                
            case 'n':  // g n = 12× (multiply by 12)
                this.multiply12();
                break;
                
            case 'i':  // g i = 12÷ (divide by 12)
                this.divide12();
                break;
                
            case 'enter':  // g ENTER = LSTx (recall last X)
                this.recallLastX();
                break;
                
            case 'digit-3':  // g 3 = n! (factorial)
                this.factorialFunc();
                break;
            
            case 'digit-7':  // g 7 = BEGIN mode
                this.setBeginMode();
                break;
                
            case 'digit-8':  // g 8 = END mode
                this.setEndMode();
                break;

            case 'pv':  // g PV = CF0
                this.handleCF0();
                break;

            case 'pmt':  // g PMT = CFj
                this.handleCFj();
                break;

            case 'fv':  // g FV = Nj
                this.handleNj();
                break;

            case 'eex':  // g EEX = ΔDYS
                this.handleDeltaDays();
                break;

            case 'digit-4':  // g 4 = D.MY
                this.dmyMode = true;
                break;

            case 'digit-5':  // g 5 = M.DY
                this.dmyMode = false;
                break;

            case 'digit-9':  // g 9 = MEM (CF count / remaining program)
                this.handleMem();
                break;

            case 'digit-0':  // g 0 = x̄
                this.handleMean();
                break;

            case 'decimal':  // g · = s
                this.handleStdDev();
                break;

            case 'digit-6':  // g 6 = x̄w
                this.handleWeightedMean();
                break;

            case 'digit-1':  // g 1 = x̂, r
                this.handlePredictX();
                break;

            case 'digit-2':  // g 2 = ŷ, r
                this.handlePredictY();
                break;

            case 'sum-plus':  // g Σ+ = Σ−
                this.handleSigmaMinus();
                break;

            case 'clx':  // g CLx = x=0 (skip next if X ≠ 0)
                this.skipNext = this.stack.x !== 0;
                break;

            case 'swap-xy':  // g x⇄y = x≤y
                this.skipNext = this.stack.x > this.stack.y;
                break;

            case 'roll-down':  // g R↓ = GTO
                this.pendingGto = true;
                this.gtoDigits = '';
                break;

            default:
                console.log('Unimplemented blue function:', key);
        }
    }

    /**
     * Enter a digit
     * @param {string} digit - Digit to enter (0-9)
     */
    enterDigit(digit) {
        // Handle pending operations (STO/RCL)
        if (this.pendingOperation === 'sto') {
            const registerNum = parseInt(digit);
            this.storeRegister(registerNum);
            this.pendingOperation = null;
            return;
        }
        
        if (this.pendingOperation === 'rcl') {
            const registerNum = parseInt(digit);
            this.recallRegister(registerNum);
            this.pendingOperation = null;
            return;
        }

        if (this.eexActive) {
            if (this.eexDigits.length < 3) this.eexDigits += digit;
            this.applyEex();
            this.tvmStoreNext = true;
            return;
        }
        
        // Normal digit entry — lift once when starting a new number after an operation
        if (this.isNewNumber) {
            if (this.stack.stackLift) this.stack.lift();
            this.currentInput = digit;
            this.isNewNumber = false;
            this.hasDecimal = false;
        } else if (this.currentInput.replace(/[^0-9]/g, "").length < 10) {
            this.currentInput += digit;
        }
        this.stack.x = parseFloat(this.currentInput) || 0;
        this.tvmStoreNext = true;
    }

    /**
     * Enter decimal point
     */
    enterDecimal() {
        if (this.isNewNumber) {
            if (this.stack.stackLift) this.stack.lift();
            this.currentInput = "0.";
            this.isNewNumber = false;
            this.hasDecimal = true;
        } else if (!this.hasDecimal) {
            this.currentInput += ".";
            this.hasDecimal = true;
        }
        this.stack.x = parseFloat(this.currentInput) || 0;
        this.tvmStoreNext = true;
    }

    /**
     * ENTER key: Push X to stack
     */
    enter() {
        this.finishEex();
        this.stack.enter();
        this.currentInput = '';
        this.isNewNumber = true;
        this.hasDecimal = false;
        this.tvmStoreNext = true;
        this.display.show(this.stack.x, true);
    }

    /**
     * Clear X register
     */
    clearX() {
        this.stack.clearX();
        this.currentInput = '';
        this.isNewNumber = true;
        this.hasDecimal = false;
        this.tvmStoreNext = true;
    }

    /**
     * Roll down stack
     */
    rollDown() {
        this.finishNumberEntry();
        this.stack.rollDown();
        this.isNewNumber = true;
    }

    /**
     * Swap X and Y
     */
    swapXY() {
        this.finishNumberEntry();
        this.stack.swapXY();
        this.isNewNumber = true;
    }

    /**
     * Addition: Y + X
     */
    add() {
        this.finishNumberEntry();
        this.stack.binaryOp((y, x) => y + x);
        this.isNewNumber = true;
    }

    /**
     * Subtraction: Y - X
     */
    subtract() {
        this.finishNumberEntry();
        this.stack.binaryOp((y, x) => y - x);
        this.isNewNumber = true;
    }

    /**
     * Multiplication: Y × X
     */
    multiply() {
        this.finishNumberEntry();
        this.stack.binaryOp((y, x) => y * x);
        this.isNewNumber = true;
    }

    /**
     * Division: Y ÷ X
     */
    divide() {
        this.finishNumberEntry();
        if (this.stack.x === 0) {
            this.display.showError('Error 0');
            return;
        }
        this.stack.binaryOp((y, x) => y / x);
        this.isNewNumber = true;
    }

    /**
     * Finish number entry (push to stack if needed)
     */
    finishNumberEntry() {
        this.finishEex();
        this.isNewNumber = true;
        this.currentInput = "";
        this.hasDecimal = false;
        this.tvmStoreNext = true;
    }

    /**
     * Change sign of X (CHS)
     */
    changeSign() {
        if (this.eexActive) {
            this.eexNeg = !this.eexNeg;
            this.applyEex();
            this.tvmStoreNext = true;
            return;
        }
        if (!this.isNewNumber) {
            // Change sign of current input
            if (this.currentInput.startsWith('-')) {
                this.currentInput = this.currentInput.substring(1);
            } else {
                this.currentInput = '-' + this.currentInput;
            }
            this.stack.x = parseFloat(this.currentInput) || 0;
        } else {
            // Change sign of stack X
            this.stack.x = -this.stack.x;
        }
        this.tvmStoreNext = true;
    }

    /**
     * Recall last X value
     */
    recallLastX() {
        this.stack.recallLastX();
        this.isNewNumber = true;
        this.tvmStoreNext = true;
    }

    // ============================================
    // MATHEMATICAL FUNCTIONS
    // ============================================

    /**
     * Percentage: X% of Y (HP-12C %). Y stays.
     */
    percent() {
        this.finishNumberEntry();
        try {
            const result = this.math.percent(this.stack.x, this.stack.y);
            this.stack.x = result;
            // Both X and Y remain on stack (no drop)
            this.isNewNumber = true;
        } catch (error) {
            this.display.showError(error.message);
        }
    }

    /**
     * Percent Total: X is what percent of Y (HP-12C %T)
     */
    percentTotal() {
        this.finishNumberEntry();
        try {
            const result = this.math.percentTotal(this.stack.x, this.stack.y);
            this.stack.x = result;
            // Both X and Y remain on stack (no drop)
            this.isNewNumber = true;
        } catch (error) {
            this.display.showError(error.message);
        }
    }

    /**
     * Delta Percent: Percentage change from Y to X
     * Formula: ((X - Y) / Y) × 100
     */
    deltaPercent() {
        this.finishNumberEntry();
        try {
            const result = this.math.deltaPercent(this.stack.x, this.stack.y);
            this.stack.x = result;
            // Both X and Y remain on stack (no drop)
            this.isNewNumber = true;
        } catch (error) {
            this.display.showError(error.message);
        }
    }

    /**
     * Reciprocal: 1 / X
     */
    reciprocal() {
        this.finishNumberEntry();
        try {
            this.stack.saveLastX();
            const result = this.math.reciprocal(this.stack.x);
            this.stack.x = result;
            this.isNewNumber = true;
        } catch (error) {
            this.display.showError(error.message);
        }
    }

    /**
     * Power: Y raised to power of X (Y^X)
     */
    power() {
        this.finishNumberEntry();
        try {
            const result = this.math.power(this.stack.y, this.stack.x);
            this.stack.binaryOp((y, x) => this.math.power(y, x));
            this.isNewNumber = true;
        } catch (error) {
            this.display.showError(error.message);
        }
    }

    /**
     * Square Root: √X
     */
    squareRoot() {
        this.finishNumberEntry();
        try {
            this.stack.saveLastX();
            const result = this.math.sqrt(this.stack.x);
            this.stack.x = result;
            this.isNewNumber = true;
        } catch (error) {
            this.display.showError(error.message);
        }
    }

    /**
     * Natural Logarithm: ln(X)
     */
    naturalLog() {
        this.finishNumberEntry();
        try {
            this.stack.saveLastX();
            const result = this.math.ln(this.stack.x);
            this.stack.x = result;
            this.isNewNumber = true;
        } catch (error) {
            this.display.showError(error.message);
        }
    }

    /**
     * Exponential: e^X
     */
    exponential() {
        this.finishNumberEntry();
        try {
            this.stack.saveLastX();
            const result = this.math.exp(this.stack.x);
            this.stack.x = result;
            this.isNewNumber = true;
        } catch (error) {
            this.display.showError(error.message);
        }
    }

    /**
     * Integer Part: Return integer portion of X
     */
    integerPart() {
        this.finishNumberEntry();
        this.stack.saveLastX();
        this.stack.x = this.math.integerPart(this.stack.x);
        this.isNewNumber = true;
    }

    /**
     * Fractional Part: Return fractional portion of X
     */
    fractionalPart() {
        this.finishNumberEntry();
        this.stack.saveLastX();
        this.stack.x = this.math.fractionalPart(this.stack.x);
        this.isNewNumber = true;
    }

    /**
     * Multiply by 12: X × 12 (for period conversions)
     */
    multiply12() {
        this.finishNumberEntry();
        this.stack.saveLastX();
        this.stack.x = this.math.multiply12(this.stack.x);
        this.isNewNumber = true;
    }

    /**
     * Divide by 12: X ÷ 12 (for rate conversions)
     */
    divide12() {
        this.finishNumberEntry();
        this.stack.saveLastX();
        this.stack.x = this.math.divide12(this.stack.x);
        this.isNewNumber = true;
    }

    /**
     * Factorial: n! (g 3)
     */
    factorialFunc() {
        this.finishNumberEntry();
        try {
            this.stack.saveLastX();
            const result = this.math.factorial(this.stack.x);
            this.stack.x = result;
            this.isNewNumber = true;
        } catch (error) {
            this.display.showError(error.message);
        }
    }

    /**
     * Store X to memory register
     * @param {number} registerNum - Register number (0-19)
     */
    storeRegister(registerNum) {
        this.finishNumberEntry();
        this.memory.store(registerNum, this.stack.x);
        console.log(`Stored ${this.stack.x} to R${registerNum}`);
    }

    /**
     * Recall value from memory register
     * @param {number} registerNum - Register number (0-19)
     */
    recallRegister(registerNum) {
        const value = this.memory.recall(registerNum);
        this.stack.push(value);
        this.isNewNumber = true;
        this.tvmStoreNext = true;
        console.log(`Recalled ${value} from R${registerNum}`);
    }

    consumePendingMemory(key) {
        if (this.pendingOperation !== 'sto' && this.pendingOperation !== 'rcl') {
            return false;
        }
        const finMap = { n: 0, i: 1, pv: 2, pmt: 3, fv: 4 };
        if (!(key in finMap)) {
            return false;
        }
        const name = key;
        this.finishNumberEntry();
        if (this.pendingOperation === 'sto') {
            this.memory.setFinancialRegister(name, this.stack.x);
            this.tvmStoreNext = false;
        } else {
            const value = this.memory.getFinancialRegister(name);
            this.stack.push(value);
            this.isNewNumber = true;
            this.tvmStoreNext = true;
        }
        this.pendingOperation = null;
        return true;
    }

    // ============================================
    // FINANCIAL TVM METHODS
    // ============================================
    
    /**
     * Handle TVM key press (n, i, PV, PMT, FV)
     * Behavior: If new number entered, store it. Otherwise, solve for the variable.
     *
     * @param {string} register - TVM register name ('n', 'i', 'pv', 'pmt', 'fv')
     */
    handleTVMKey(register) {
        const registerName = register.toUpperCase();

        if (this.tvmStoreNext) {
            const value = this.stack.x;
            this.memory.setFinancialRegister(register, value);
            this.isNewNumber = true;
            this.currentInput = '';
            this.tvmStoreNext = false;
            console.log(`Stored ${value} in ${registerName}`);
            this.updateDisplay();
        } else {
            // Solve mode: calculate the register value
            try {
                let result;
                let methodName;
                
                switch(register) {
                    case 'n':
                        result = Math.ceil(this.financial.solveN(this.memory));
                        methodName = 'n';
                        break;
                    case 'i':
                        result = this.financial.solveI(this.memory);
                        methodName = 'i';
                        break;
                    case 'pv':
                        result = this.financial.solvePV(this.memory);
                        methodName = 'PV';
                        break;
                    case 'pmt':
                        result = this.financial.solvePMT(this.memory);
                        methodName = 'PMT';
                        break;
                    case 'fv':
                        result = this.financial.solveFV(this.memory);
                        methodName = 'FV';
                        break;
                }
                
                // Store result in register
                this.memory.setFinancialRegister(register, result);
                
                // Push to stack and display
                this.stack.x = result;
                this.isNewNumber = true;
                this.currentInput = '';
                this.tvmStoreNext = false;
                
                // Show iteration count for iterative solvers
                if (register === 'n' || register === 'i') {
                    const iterations = this.financial.getLastIterationCount();
                    console.log(`Solved ${registerName} = ${result} (${iterations} iterations)`);
                } else {
                    console.log(`Solved ${registerName} = ${result}`);
                }
                
                this.updateDisplay();
            } catch (error) {
                console.error(`Error solving ${registerName}:`, error.message);
                this.display.showError(error.message);
            }
        }
    }
    
    /**
     * Get financial register number for a given register name
     * @param {string} register - Register name
     * @returns {number} Register number (0-4)
     */
    getFinancialRegisterNumber(register) {
        const mapping = { 'n': 0, 'i': 1, 'pv': 2, 'pmt': 3, 'fv': 4 };
        return mapping[register.toLowerCase()] || 0;
    }
    
    /**
     * Set BEGIN mode (payments at start of period)
     */
    setBeginMode() {
        this.financial.setPaymentMode('BEGIN');
        this.display.setIndicator('begin', true);
        console.log('Payment mode: BEGIN (annuity due)');
    }
    
    /**
     * Set END mode (payments at end of period)
     */
    setEndMode() {
        this.financial.setPaymentMode('END');
        this.display.setIndicator('begin', false);
        console.log('Payment mode: END (ordinary annuity)');
    }
    
    handleCF0() {
        this.finishNumberEntry();
        this.memory.setCF0(this.stack.x);
        this.isNewNumber = true;
        this.tvmStoreNext = false;
        this.updateDisplay();
    }

    handleCFj() {
        this.finishNumberEntry();
        this.memory.appendCFj(this.stack.x);
        this.isNewNumber = true;
        this.tvmStoreNext = false;
        this.updateDisplay();
    }

    handleNj() {
        this.finishNumberEntry();
        try {
            this.memory.setLastNj(this.stack.x);
            this.isNewNumber = true;
            this.tvmStoreNext = false;
            this.updateDisplay();
        } catch (error) {
            this.display.showError(error.message);
        }
    }

    handleNPV() {
        this.finishNumberEntry();
        try {
            const result = this.financial.calculateNPV(this.memory);
            this.stack.saveLastX();
            this.stack.x = result;
            this.isNewNumber = true;
            this.tvmStoreNext = true;
            this.updateDisplay();
        } catch (error) {
            this.display.showError(error.message);
        }
    }

    handleRound() {
        this.finishNumberEntry();
        const d = Math.max(0, this.display.decimals | 0);
        const f = Math.pow(10, d);
        this.stack.saveLastX();
        this.stack.x = Math.round(this.stack.x * f) / f;
        this.isNewNumber = true;
        this.tvmStoreNext = true;
        this.updateDisplay();
    }

    handleIRR() {
        this.finishNumberEntry();
        try {
            const result = this.financial.calculateIRR(this.memory);
            this.stack.saveLastX();
            this.stack.x = result;
            this.memory.setFinancialRegister('i', result);
            this.isNewNumber = true;
            this.tvmStoreNext = true;
            this.updateDisplay();
        } catch (error) {
            this.display.showError(error.message);
        }
    }

    /**
     * Handle amortization calculation
     * HP-12C workflow:
     *   1 [ENTER] 12 [f] [AMORT]  → Interest for periods 1-12
     *   [x⇄y]                      → Principal paid
     *   [RCL] [PV]                 → Remaining balance
     *
     * Expects: Y register = start period, X register = end period
     */
    handleAmortization() {
        this.finishNumberEntry();
        
        try {
            // Get periods from stack
            const endPeriod = Math.floor(this.stack.x);    // X = end period
            const startPeriod = Math.floor(this.stack.y);  // Y = start period
            
            // Calculate amortization
            const result = this.financial.calculateAmortization(
                this.memory,
                startPeriod,
                endPeriod
            );
            
            // HP-12C display behavior:
            // - Display shows interest paid (primary result)
            // - Principal is in Y register (accessible via x⇄y)
            // - Balance updates PV register
            
            // Store principal in Y register for x⇄y access
            this.stack.y = result.principalPaid;
            
            // Display interest in X register
            this.stack.x = result.interestPaid;
            
            // Update PV register with new balance
            this.memory.setFinancialRegister('pv', result.balance);
            
            this.isNewNumber = true;
            this.currentInput = '';
            
            console.log(`AMORT periods ${startPeriod}-${endPeriod}:`);
            console.log(`  Interest: ${result.interestPaid.toFixed(2)}`);
            console.log(`  Principal: ${result.principalPaid.toFixed(2)}`);
            console.log(`  Balance: ${result.balance.toFixed(2)}`);
            
            this.updateDisplay();
        } catch (error) {
            console.error('Amortization error:', error.message);
            this.display.showError(error.message);
        }
    }

    // ============================================
    // SYSTEM METHODS
    // ============================================
    
    handleEex() {
        if (this.eexActive) return;
        this.eexMantissa = this.isNewNumber ? (this.stack.x || 1) : (parseFloat(this.currentInput) || 0);
        if (this.isNewNumber && this.stack.stackLift) this.stack.lift();
        this.eexActive = true;
        this.eexDigits = '';
        this.eexNeg = false;
        this.isNewNumber = false;
        this.tvmStoreNext = true;
        this.applyEex();
    }

    applyEex() {
        const exp = parseInt(this.eexDigits || '0', 10) * (this.eexNeg ? -1 : 1);
        this.stack.x = this.eexMantissa * Math.pow(10, exp);
    }

    finishEex() {
        if (!this.eexActive) return;
        this.applyEex();
        this.eexActive = false;
        this.eexDigits = '';
        this.eexNeg = false;
        this.currentInput = String(this.stack.x);
    }

    handleSimpleInterest() {
        this.finishNumberEntry();
        const n = this.memory.getFinancialRegister('n');
        const i = this.memory.getFinancialRegister('i');
        const pv = this.memory.getFinancialRegister('pv');
        const i360 = -pv * (i / 100) * (n / 360);
        const i365 = -pv * (i / 100) * (n / 365);
        this.stack.saveLastX();
        this.stack.z = i365;
        this.stack.y = Math.abs(pv);
        this.stack.x = i360;
        this.stack.stackLift = true;
        this.isNewNumber = true;
        this.tvmStoreNext = true;
    }

    handleDateAdd() {
        this.finishNumberEntry();
        const H = window.HpHandbook;
        const base = H.parsePacked(this.stack.y, this.dmyMode);
        if (!base) { this.display.showError('Error 8'); return; }
        const out = H.addDays(base, Math.round(this.stack.x));
        this.stack.saveLastX();
        this.stack.y = H.dayOfWeek(out);
        this.stack.x = H.packDate(out, this.dmyMode);
        this.display.overrideDecimals = 6;
        this.isNewNumber = true;
        this.tvmStoreNext = true;
    }

    handleDeltaDays() {
        this.finishNumberEntry();
        const H = window.HpHandbook;
        const a = H.parsePacked(this.stack.y, this.dmyMode);
        const b = H.parsePacked(this.stack.x, this.dmyMode);
        if (!a || !b) { this.display.showError('Error 8'); return; }
        this.stack.saveLastX();
        this.stack.y = H.days360(a, b);
        this.stack.x = H.daysActual(a, b);
        this.isNewNumber = true;
        this.tvmStoreNext = true;
    }

    handleSigmaPlus() {
        this.finishNumberEntry();
        const n = window.HpHandbook.sigmaPlus(this.memory, this.stack.x, this.stack.y);
        this.stack.x = n;
        this.isNewNumber = true;
        this.tvmStoreNext = true;
        this.stack.stackLift = false;
    }

    handleSigmaMinus() {
        this.finishNumberEntry();
        const n = window.HpHandbook.sigmaMinus(this.memory, this.stack.x, this.stack.y);
        this.stack.x = n;
        this.isNewNumber = true;
        this.tvmStoreNext = true;
        this.stack.stackLift = false;
    }

    handleMean() {
        this.finishNumberEntry();
        try {
            const mx = window.HpHandbook.meanX(this.memory);
            const my = window.HpHandbook.meanY(this.memory);
            this.stack.saveLastX();
            this.stack.y = my;
            this.stack.x = mx;
            this.isNewNumber = true;
            this.tvmStoreNext = true;
        } catch (e) { this.display.showError(e.message); }
    }

    handleStdDev() {
        this.finishNumberEntry();
        try {
            const sx = window.HpHandbook.stdX(this.memory);
            const sy = window.HpHandbook.stdY(this.memory);
            this.stack.saveLastX();
            this.stack.y = sy;
            this.stack.x = sx;
            this.isNewNumber = true;
            this.tvmStoreNext = true;
        } catch (e) { this.display.showError(e.message); }
    }

    handleWeightedMean() {
        this.finishNumberEntry();
        try {
            this.stack.saveLastX();
            this.stack.x = window.HpHandbook.weightedMeanX(this.memory);
            this.isNewNumber = true;
            this.tvmStoreNext = true;
        } catch (e) { this.display.showError(e.message); }
    }

    handlePredictY() {
        this.finishNumberEntry();
        try {
            const lr = window.HpHandbook.linReg(this.memory);
            const yhat = lr.slope * this.stack.x + lr.intercept;
            this.stack.saveLastX();
            this.stack.y = lr.r;
            this.stack.x = yhat;
            this.isNewNumber = true;
            this.tvmStoreNext = true;
        } catch (e) { this.display.showError(e.message); }
    }

    handlePredictX() {
        this.finishNumberEntry();
        try {
            const lr = window.HpHandbook.linReg(this.memory);
            if (lr.slope === 0) throw new Error('Error 2');
            const xhat = (this.stack.x - lr.intercept) / lr.slope;
            this.stack.saveLastX();
            this.stack.y = lr.r;
            this.stack.x = xhat;
            this.isNewNumber = true;
            this.tvmStoreNext = true;
        } catch (e) { this.display.showError(e.message); }
    }

    handleDepr(kind) {
        this.finishNumberEntry();
        try {
            const cost = this.memory.getFinancialRegister('pv');
            const salvage = this.memory.getFinancialRegister('fv');
            const life = this.memory.getFinancialRegister('n');
            const year = Math.round(Math.abs(this.stack.x));
            const db = this.memory.getFinancialRegister('i');
            let r;
            if (kind === 'sl') r = window.HpHandbook.deprSL(cost, salvage, life, year);
            else if (kind === 'soyd') r = window.HpHandbook.deprSOYD(cost, salvage, life, year);
            else r = window.HpHandbook.deprDB(cost, salvage, life, db, year);
            this.stack.saveLastX();
            this.stack.y = r.remaining;
            this.stack.x = r.depr;
            this.isNewNumber = true;
            this.tvmStoreNext = true;
        } catch (e) { this.display.showError(e.message); }
    }

    handleBondPrice() {
        this.finishNumberEntry();
        try {
            const H = window.HpHandbook;
            const settle = H.parsePacked(this.stack.y, this.dmyMode);
            const mat = H.parsePacked(this.stack.x, this.dmyMode);
            if (!settle || !mat) throw new Error('Error 8');
            const coupon = this.memory.getFinancialRegister('pmt');
            const yld = this.memory.getFinancialRegister('i');
            const bp = H.bondPrice(settle, mat, coupon, yld);
            this.stack.saveLastX();
            this.stack.y = bp.accrued;
            this.stack.x = bp.clean;
            this.isNewNumber = true;
            this.tvmStoreNext = true;
        } catch (e) { this.display.showError(e.message); }
    }

    handleBondYtm() {
        this.finishNumberEntry();
        try {
            const H = window.HpHandbook;
            const settle = H.parsePacked(this.stack.y, this.dmyMode);
            const mat = H.parsePacked(this.stack.x, this.dmyMode);
            if (!settle || !mat) throw new Error('Error 8');
            const coupon = this.memory.getFinancialRegister('pmt');
            const price = this.memory.getFinancialRegister('pv');
            const yld = H.bondYield(settle, mat, coupon, price);
            this.stack.saveLastX();
            this.stack.x = yld;
            this.memory.setFinancialRegister('i', yld);
            this.isNewNumber = true;
            this.tvmStoreNext = true;
        } catch (e) { this.display.showError(e.message); }
    }

    handleMem() {
        this.finishNumberEntry();
        const cfs = (this.memory.cashFlows || []).length;
        const cfCount = Math.max(0, cfs - 1);
        this.stack.y = cfCount;
        this.stack.x = 99 - this.program.length;
        this.isNewNumber = true;
        this.tvmStoreNext = true;
    }

    recordStep(key) {
        if (this.program.length >= 99) return;
        this.program.push({
            key: key,
            f: this.prefixF,
            g: this.prefixG,
            addr: 0,
        });
        this.pc = this.program.length;
    }

    executeStep(step) {
        if (!step) return;
        if (step.g && step.key === 'roll-down') {
            this.pc = Math.max(0, (step.addr || 1) - 1);
            return 'goto';
        }
        if (step.f) {
            this.handleGoldFunction(step.key);
            this.prefixF = false;
        } else if (step.g) {
            this.handleBlueFunction(step.key);
            this.prefixG = false;
        } else {
            this.handlePrimaryFunction(step.key, step.key);
        }
        return null;
    }

    runProgram() {
        if (this.prgmMode) return;
        if (!this.program.length) return;
        this.running = true;
        let guard = 0;
        if (this.pc >= this.program.length) this.pc = 0;
        while (this.pc < this.program.length && guard++ < 5000) {
            if (this.skipNext) {
                this.skipNext = false;
                this.pc += 1;
                continue;
            }
            const step = this.program[this.pc];
            if (!step.f && !step.g && step.key === 'run-stop') break;
            const jumped = this.executeStep(step);
            if (jumped !== 'goto') this.pc += 1;
        }
        this.running = false;
        this.isNewNumber = true;
    }

    sstRun() {
        if (this.prgmMode) return;
        if (this.pc >= this.program.length) this.pc = 0;
        if (!this.program.length) return;
        const step = this.program[this.pc];
        this.pc += 1;
        if (this.skipNext) { this.skipNext = false; return; }
        this.executeStep(step);
        this.isNewNumber = true;
    }

    /**
     * Reset calculator
     */
    reset() {
        this.stack.reset();
        this.memory.reset();
        this.currentInput = '';
        this.isNewNumber = true;
        this.hasDecimal = false;
        this.prefixF = false;
        this.prefixG = false;
        this.pendingOperation = null;
        this.tvmStoreNext = false;
        this.dmyMode = false;
        this.eexActive = false;
        this.eexDigits = '';
        this.eexNeg = false;
        this.skipNext = false;
        this.pendingGto = false;
        this.gtoDigits = '';
        this.display.setFormat('fixed', 2);
        this.display.setIndicator('f', false);
        this.display.setIndicator('g', false);
        console.log('Calculator reset');
    }

    /**
     * Update display with current value
     */
    updateDisplay() {
        this.display.show(this.stack.x);
        
        // Update stack display if visible
        const stackDisplay = document.getElementById('stackDisplay');
        if (stackDisplay && stackDisplay.style.display !== 'none') {
            this.display.updateStackDisplay(this.stack.getState());
        }
    }

    /**
     * Get calculator state
     * @returns {object} Complete calculator state
     */
    getState() {
        return {
            stack: this.stack.getState(),
            memory: this.memory.getState(),
            display: this.display.getFormat(),
            prefixF: this.prefixF,
            prefixG: this.prefixG
        };
    }
}

/* DOM auto-init disabled — Casio app owns the UI */
