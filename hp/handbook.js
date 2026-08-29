/**
 * HP-12C handbook extras: dates, stats, depreciation, bonds.
 * Ported from cardputer-fin-calc (dates/depr/bond/sigma) to match Owner's Handbook.
 */
(function (global) {
  function isLeap(y) {
    return (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0;
  }
  function dim(y, m) {
    const d = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1];
    if (!d) return 0;
    return m === 2 && isLeap(y) ? 29 : d;
  }
  function toSerial(dt) {
    let y = dt.y, m = dt.m, d = dt.d;
    if (m <= 2) { y -= 1; m += 12; }
    const era = Math.floor((y >= 0 ? y : y - 399) / 400);
    const yoe = y - era * 400;
    const doy = Math.floor((153 * (m - 3) + 2) / 5) + d - 1;
    const doe = yoe * 365 + Math.floor(yoe / 4) - Math.floor(yoe / 100) + doy;
    return era * 146097 + doe - 719468;
  }
  function fromSerial(days) {
    let z = days + 719468;
    const era = Math.floor((z >= 0 ? z : z - 146096) / 146097);
    const doe = z - era * 146097;
    const yoe = Math.floor((doe - Math.floor(doe / 1460) + Math.floor(doe / 36524) - Math.floor(doe / 146096)) / 365);
    let y = yoe + era * 400;
    const doy = doe - (365 * yoe + Math.floor(yoe / 4) - Math.floor(yoe / 100));
    const mp = Math.floor((5 * doy + 2) / 153);
    const d = doy - Math.floor((153 * mp + 2) / 5) + 1;
    let m = mp < 10 ? mp + 3 : mp - 9;
    if (m <= 2) y += 1;
    return { y: y, m: m, d: d };
  }
  function valid(dt) {
    return dt && dt.m >= 1 && dt.m <= 12 && dt.d >= 1 && dt.d <= dim(dt.y, dt.m);
  }
  function parsePacked(v, dmy) {
    const av = Math.abs(v);
    const ipart = Math.floor(av);
    const packed = Math.round((av - ipart) * 1e6);
    const leading = ipart * (v < 0 ? -1 : 1);
    const mid = Math.floor(packed / 10000);
    const year = packed % 10000;
    const out = dmy
      ? { d: leading, m: mid, y: year }
      : { m: leading, d: mid, y: year };
    return valid(out) ? out : null;
  }
  function packDate(dt, dmy) {
    const leading = dmy ? dt.d : dt.m;
    const second = dmy ? dt.m : dt.d;
    return leading + (second * 10000 + dt.y) / 1e6;
  }
  function dayOfWeek(dt) {
    const s = toSerial(dt);
    return ((s % 7) + 7 + 4) % 7; // 0=Sun
  }
  function daysActual(a, b) { return toSerial(b) - toSerial(a); }
  function days360(a, b) {
    let d1 = a.d, d2 = b.d;
    if (d1 === 31) d1 = 30;
    if (d2 === 31 && d1 === 30) d2 = 30;
    return (b.y - a.y) * 360 + (b.m - a.m) * 30 + (d2 - d1);
  }
  function addDays(base, n) { return fromSerial(toSerial(base) + n); }

  function sigmaPlus(mem, x, y) {
    mem.store(1, (mem.recall(1) || 0) + 1);
    mem.store(2, (mem.recall(2) || 0) + x);
    mem.store(3, (mem.recall(3) || 0) + x * x);
    mem.store(4, (mem.recall(4) || 0) + y);
    mem.store(5, (mem.recall(5) || 0) + y * y);
    mem.store(6, (mem.recall(6) || 0) + x * y);
    return mem.recall(1);
  }
  function sigmaMinus(mem, x, y) {
    mem.store(1, (mem.recall(1) || 0) - 1);
    mem.store(2, (mem.recall(2) || 0) - x);
    mem.store(3, (mem.recall(3) || 0) - x * x);
    mem.store(4, (mem.recall(4) || 0) - y);
    mem.store(5, (mem.recall(5) || 0) - y * y);
    mem.store(6, (mem.recall(6) || 0) - x * y);
    return mem.recall(1);
  }
  function N(mem) { return mem.recall(1) || 0; }
  function Sx(mem) { return mem.recall(2) || 0; }
  function Sxx(mem) { return mem.recall(3) || 0; }
  function Sy(mem) { return mem.recall(4) || 0; }
  function Syy(mem) { return mem.recall(5) || 0; }
  function Sxy(mem) { return mem.recall(6) || 0; }

  function meanX(mem) { const n = N(mem); if (n <= 0) throw new Error("Error 2"); return Sx(mem) / n; }
  function meanY(mem) { const n = N(mem); if (n <= 0) throw new Error("Error 2"); return Sy(mem) / n; }
  function stdX(mem) {
    const n = N(mem);
    if (n < 2) throw new Error("Error 2");
    let v = (Sxx(mem) - Sx(mem) * Sx(mem) / n) / (n - 1);
    if (v < 0) v = 0;
    return Math.sqrt(v);
  }
  function stdY(mem) {
    const n = N(mem);
    if (n < 2) throw new Error("Error 2");
    let v = (Syy(mem) - Sy(mem) * Sy(mem) / n) / (n - 1);
    if (v < 0) v = 0;
    return Math.sqrt(v);
  }
  function weightedMeanX(mem) {
    const sy = Sy(mem);
    if (sy === 0) throw new Error("Error 2");
    return Sxy(mem) / sy;
  }
  function linReg(mem) {
    const n = N(mem);
    if (n < 2) throw new Error("Error 2");
    const dx = n * Sxx(mem) - Sx(mem) * Sx(mem);
    const dy = n * Syy(mem) - Sy(mem) * Sy(mem);
    const cov = n * Sxy(mem) - Sx(mem) * Sy(mem);
    if (dx === 0) throw new Error("Error 2");
    const slope = cov / dx;
    const intercept = (Sy(mem) - slope * Sx(mem)) / n;
    const r = dy > 0 ? cov / Math.sqrt(dx * dy) : 0;
    return { slope: slope, intercept: intercept, r: r };
  }

  function deprSL(cost, salvage, life, year) {
    if (life <= 0 || year < 1 || year > life) throw new Error("Error 5");
    const dep = (cost - salvage) / life;
    let remaining = (cost - salvage) - dep * year;
    if (remaining < 0) remaining = 0;
    return { depr: dep, remaining: remaining };
  }
  function deprSOYD(cost, salvage, life, year) {
    if (life <= 0 || year < 1 || year > life) throw new Error("Error 5");
    const depreciable = cost - salvage;
    const soyd = life * (life + 1) / 2;
    const depr = depreciable * (life - year + 1) / soyd;
    let consumed = 0;
    for (let k = 1; k <= year; k++) consumed += (life - k + 1) / soyd;
    let remaining = depreciable * (1 - consumed);
    if (remaining < 0) remaining = 0;
    return { depr: depr, remaining: remaining };
  }
  function deprDB(cost, salvage, life, dbPct, year) {
    if (life <= 0 || year < 1 || year > life || dbPct <= 0) throw new Error("Error 5");
    const rate = (dbPct / 100) / life;
    let book = cost, depr = 0;
    for (let k = 1; k <= year; k++) {
      let d = book * rate;
      if (book - d < salvage) d = book - salvage;
      if (d < 0) d = 0;
      if (k === year) depr = d;
      book -= d;
    }
    let remaining = book - salvage;
    if (remaining < 0) remaining = 0;
    return { depr: depr, remaining: remaining };
  }

  function prevCoupon(settlement, maturity) {
    let c = { y: maturity.y, m: maturity.m, d: maturity.d };
    for (let i = 0; i < 80; i++) {
      const prev = { y: c.y, m: c.m - 6, d: c.d };
      if (prev.m <= 0) { prev.m += 12; prev.y -= 1; }
      const dmax = dim(prev.y, prev.m);
      if (prev.d > dmax) prev.d = dmax;
      if (daysActual(prev, settlement) >= 0) return prev;
      c = prev;
    }
    return settlement;
  }
  function addMonths(dt, months) {
    const out = { y: dt.y, m: dt.m + months, d: dt.d };
    while (out.m > 12) { out.m -= 12; out.y += 1; }
    while (out.m < 1) { out.m += 12; out.y -= 1; }
    const dmax = dim(out.y, out.m);
    if (out.d > dmax) out.d = dmax;
    return out;
  }
  function bondPrice(settlement, maturity, coupon, yld) {
    if (!valid(settlement) || !valid(maturity)) throw new Error("Error 8");
    if (daysActual(settlement, maturity) <= 0) throw new Error("Error 8");
    const prev = prevCoupon(settlement, maturity);
    const next = addMonths(prev, 6);
    const e = days360(prev, next);
    const a = days360(prev, settlement);
    if (e <= 0) throw new Error("Error 8");
    const f = a / e;
    const c = coupon / 2;
    const y = yld / 200;
    let N = 0;
    let d = { y: next.y, m: next.m, d: next.d };
    while (N < 200) {
      N += 1;
      if (d.y === maturity.y && d.m === maturity.m && d.d === maturity.d) break;
      const nx = addMonths(d, 6);
      if (daysActual(nx, maturity) < 0) { N += 1; break; }
      d = nx;
    }
    let pvCoupons = 0;
    for (let k = 1; k <= N; k++) {
      pvCoupons += c / Math.pow(1 + y, k - f);
    }
    const pvRedemp = 100 / Math.pow(1 + y, N - f);
    const dirty = pvCoupons + pvRedemp;
    const accrued = c * f;
    return { clean: dirty - accrued, accrued: accrued };
  }
  function bondYield(settlement, maturity, coupon, price) {
    let lo = -0.5, hi = 50, fLo = bondPrice(settlement, maturity, coupon, lo).clean - price;
    for (let i = 0; i < 60; i++) {
      const mid = 0.5 * (lo + hi);
      const fm = bondPrice(settlement, maturity, coupon, mid).clean - price;
      if (Math.abs(fm) < 1e-8) return mid;
      if (fm * fLo < 0) hi = mid;
      else { lo = mid; fLo = fm; }
    }
    return 0.5 * (lo + hi);
  }

  global.HpHandbook = {
    parsePacked: parsePacked,
    packDate: packDate,
    dayOfWeek: dayOfWeek,
    daysActual: daysActual,
    days360: days360,
    addDays: addDays,
    sigmaPlus: sigmaPlus,
    sigmaMinus: sigmaMinus,
    meanX: meanX,
    meanY: meanY,
    stdX: stdX,
    stdY: stdY,
    weightedMeanX: weightedMeanX,
    linReg: linReg,
    deprSL: deprSL,
    deprSOYD: deprSOYD,
    deprDB: deprDB,
    bondPrice: bondPrice,
    bondYield: bondYield,
  };
})(typeof window !== "undefined" ? window : globalThis);
