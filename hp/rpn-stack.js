/**
 * HP-12C RPN Stack Engine
 * Manages 4-level stack (X, Y, Z, T registers) with automatic lift/drop
 */

class RPNStack {
    constructor() {
        this.x = 0;      // Display register
        this.y = 0;      // Second level
        this.z = 0;      // Third level
        this.t = 0;      // Top level
        this.lastX = 0;  // Last X value (for LSTX function)
        this.stackLift = true;  // Stack lift enable flag
    }

    /**
     * Push value onto stack (with automatic lift)
     * @param {number} value - Value to push
     */
    push(value) {
        if (this.stackLift) {
            this.lift();
        }
        this.x = value;
        this.stackLift = true;
    }

    /**
     * Pop value from stack (return X and drop stack)
     * @returns {number} X register value
     */
    pop() {
        const value = this.x;
        this.drop();
        return value;
    }

    /**
     * Lift stack (T is lost, X duplicates to Y)
     */
    lift() {
        this.t = this.z;
        this.z = this.y;
        this.y = this.x;
        // X stays the same
    }

    /**
     * Drop stack (T duplicates down)
     */
    drop() {
        this.x = this.y;
        this.y = this.z;
        this.z = this.t;
        // T stays the same
    }

    /**
     * Roll down: X->T, Y->X, Z->Y, T->Z
     */
    rollDown() {
        const temp = this.x;
        this.x = this.y;
        this.y = this.z;
        this.z = this.t;
        this.t = temp;
        this.stackLift = true;
    }

    /**
     * Swap X and Y registers
     */
    swapXY() {
        const temp = this.x;
        this.x = this.y;
        this.y = temp;
        this.stackLift = true;
    }

    /**
     * ENTER: always lift (X duplicates into Y) then disable stack lift
     * so the next typed number overwrites X instead of pushing.
     */
    enter() {
        this.lift();
        this.stackLift = false;
    }

    /**
     * Clear X register
     */
    clearX() {
        this.x = 0;
        this.stackLift = false;
    }

    /**
     * Save current X to lastX before operation
     */
    saveLastX() {
        this.lastX = this.x;
    }

    /**
     * Recall last X value
     */
    recallLastX() {
        this.push(this.lastX);
    }

    /**
     * Perform binary operation (consumes X and Y, result in X)
     * @param {function} operation - Function that takes (y, x) and returns result
     */
    binaryOp(operation) {
        this.saveLastX();
        const result = operation(this.y, this.x);
        this.drop();
        this.x = result;
        this.stackLift = true;
        return result;
    }

    /**
     * Perform unary operation (operates on X only)
     * @param {function} operation - Function that takes (x) and returns result
     */
    unaryOp(operation) {
        this.saveLastX();
        this.x = operation(this.x);
        this.stackLift = true;
        return this.x;
    }

    /**
     * Get current stack state
     * @returns {object} Stack state
     */
    getState() {
        return {
            x: this.x,
            y: this.y,
            z: this.z,
            t: this.t,
            lastX: this.lastX,
            stackLift: this.stackLift
        };
    }

    /**
     * Set stack state
     * @param {object} state - Stack state to restore
     */
    setState(state) {
        this.x = state.x || 0;
        this.y = state.y || 0;
        this.z = state.z || 0;
        this.t = state.t || 0;
        this.lastX = state.lastX || 0;
        this.stackLift = state.stackLift !== undefined ? state.stackLift : true;
    }

    /**
     * Reset stack to initial state
     */
    reset() {
        this.x = 0;
        this.y = 0;
        this.z = 0;
        this.t = 0;
        this.lastX = 0;
        this.stackLift = true;
    }

    /**
     * Disable stack lift (used after ENTER and CLx)
     */
    disableStackLift() {
        this.stackLift = false;
    }

    /**
     * Enable stack lift
     */
    enableStackLift() {
        this.stackLift = true;
    }
}
