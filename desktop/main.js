const { app, BrowserWindow, Menu } = require("electron");
const path = require("path");

const SIZES = {
  casio: [430, 760],
  hp12c: [812, 520],
  ti30xa: [390, 720],
};

let mainWindow;
let model = "hp12c";

function www(...parts) {
  return path.join(__dirname, "www", ...parts);
}

function applySize(win, m) {
  const [w, h] = SIZES[m] || SIZES.hp12c;
  win.setMinimumSize(Math.round(w * 0.72), Math.round(h * 0.72));
  win.setAspectRatio(w / h);
  win.setSize(w, h);
  win.center();
}

function bootJs(m) {
  return `
    document.documentElement.classList.add('app');
    document.documentElement.setAttribute('data-model', ${JSON.stringify(m)});
    if (window.CasioCalc && CasioCalc.setModel) CasioCalc.setModel(${JSON.stringify(m)});
  `;
}

function createWindow() {
  const [w, h] = SIZES[model];
  mainWindow = new BrowserWindow({
    width: w,
    height: h,
    title: "HP12CFULL",
    backgroundColor: "#080808",
    autoHideMenuBar: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
    },
  });
  mainWindow.loadFile(www("index.html"));
  mainWindow.webContents.on("did-finish-load", () => {
    mainWindow.webContents.executeJavaScript(bootJs(model));
  });
  applySize(mainWindow, model);
  buildMenu();
}

function setModel(next) {
  model = next;
  if (!mainWindow) return;
  applySize(mainWindow, model);
  mainWindow.webContents.executeJavaScript(bootJs(model));
  const titles = { casio: "CASIO SL-300", hp12c: "HP12CFULL", ti30xa: "TI-30Xa" };
  mainWindow.setTitle(titles[model] || "HP12CFULL");
  buildMenu();
}

function buildMenu() {
  const template = [
    {
      label: "HP12CFULL",
      submenu: [
        { role: "about" },
        { type: "separator" },
        { role: "quit" },
      ],
    },
    {
      label: "Model",
      submenu: [
        {
          label: "HP-12C",
          type: "radio",
          checked: model === "hp12c",
          click: () => setModel("hp12c"),
        },
        {
          label: "Casio SL-300",
          type: "radio",
          checked: model === "casio",
          click: () => setModel("casio"),
        },
        {
          label: "TI-30Xa",
          type: "radio",
          checked: model === "ti30xa",
          click: () => setModel("ti30xa"),
        },
      ],
    },
    { label: "Edycja", submenu: [{ role: "copy" }, { role: "selectAll" }] },
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => app.quit());
