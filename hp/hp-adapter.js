/**
 * Bridge: our photo hotspots → apezoo HP-12C engine (RPN + TVM).
 * Source: github.com/apezoo/hp-12c (vendored in this folder).
 */
(function () {
  const MAP = {
    0: "digit-0", 1: "digit-1", 2: "digit-2", 3: "digit-3", 4: "digit-4",
    5: "digit-5", 6: "digit-6", 7: "digit-7", 8: "digit-8", 9: "digit-9",
    ",": "decimal",
    "=": "enter",
    AC: "clx",
    "+/-": "chs",
    "+": "op-add",
    "−": "op-subtract",
    "×": "op-multiply",
    "÷": "op-divide",
    "%": "percent",
    mode: "on",
    n: "n",
    i: "i",
    pv: "pv",
    pmt: "pmt",
    fv: "fv",
    f: "prefix-f",
    g: "prefix-g",
    sto: "sto",
    rcl: "rcl",
    xy: "swap-xy",
    rdn: "roll-down",
    yx: "power-yx",
    recip: "reciprocal",
    pctt: "percent-total",
    dlt: "delta-percent",
    eex: "eex",
    rs: "run-stop",
    sst: "sst",
    sigma: "sum-plus",
  };

  function dummyEl() {
    return { textContent: "", classList: { add: function () {}, remove: function () {} } };
  }

  function fakeButton(mapped) {
    return {
      dataset: { key: mapped, primary: mapped },
      classList: { add: function () {}, remove: function () {} },
    };
  }

  function syncDisplay() {
    const calc = window._hpCalc;
    if (!calc || typeof window.hpPaint !== "function") return;
    const errEl = calc.display.displayElement;
    const raw =
      (errEl && /^Error/i.test(String(errEl.textContent))) || calc._suppressDisplay
        ? String(errEl.textContent || "Error 0")
        : calc.display.formatNumber(calc.stack.x);
    window.hpPaint(raw, calc);
  }

  window.hpInit = function () {
    if (window._hpCalc) return window._hpCalc;
    const calc = new Calculator();
    calc.display.displayElement = dummyEl();
    calc.display.indicatorElements = {};
    const origShow = calc.display.show.bind(calc.display);
    calc.display.show = function (value, flash) {
      origShow(value, flash);
      syncDisplay();
    };
    const origErr = calc.display.showError.bind(calc.display);
    calc.display.showError = function (msg) {
      calc._suppressDisplay = true;
      origErr(msg);
      syncDisplay();
    };
    const origUpdate = calc.updateDisplay.bind(calc);
    calc.updateDisplay = function () {
      if (this._suppressDisplay) {
        this._suppressDisplay = false;
        return;
      }
      origUpdate();
    };
    calc.reset();
    window._hpCalc = calc;
    syncDisplay();
    return calc;
  };

  window.hpPress = function (ourKey) {
    const mapped = MAP[ourKey];
    if (!mapped) return;
    const calc = window.hpInit();
    calc.handleButtonClick(fakeButton(mapped));
    syncDisplay();
  };
})();
