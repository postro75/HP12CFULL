import Cocoa
import WebKit

final class NoMenuWebView: WKWebView {
  override func willOpenMenu(_ menu: NSMenu, with event: NSEvent) {
    menu.removeAllItems()
  }
}

final class AppDelegate: NSObject, NSApplicationDelegate, WKNavigationDelegate {
  var window: NSWindow?
  var webView: WKWebView?
  private var lcdItems: [String: NSMenuItem] = [:]
  private var fontItems: [String: NSMenuItem] = [:]

  private var lcd: String {
    get { UserDefaults.standard.string(forKey: "casio.lcd") ?? "green" }
    set { UserDefaults.standard.set(newValue, forKey: "casio.lcd") }
  }
  private var font: String {
    get { UserDefaults.standard.string(forKey: "casio.font") ?? "modern" }
    set { UserDefaults.standard.set(newValue, forKey: "casio.font") }
  }

  func applicationWillFinishLaunching(_ notification: Notification) {
    buildMenu()
  }

  func applicationDidFinishLaunching(_ notification: Notification) {
    let width: CGFloat = 430
    let height: CGFloat = 760
    let window = NSWindow(
      contentRect: NSRect(x: 0, y: 0, width: width, height: height),
      styleMask: [.titled, .closable, .miniaturizable, .resizable],
      backing: .buffered,
      defer: false
    )
    window.title = "CASIO SL-300"
    window.isMovableByWindowBackground = true
    window.backgroundColor = NSColor(calibratedWhite: 0.03, alpha: 1)
    window.collectionBehavior = [.moveToActiveSpace, .fullScreenNone]
    window.isReleasedWhenClosed = false
    window.tabbingMode = .disallowed
    window.minSize = NSSize(width: 320, height: 520)
    window.aspectRatio = NSSize(width: 430, height: 788)

    let config = WKWebViewConfiguration()
    let boot = """
    document.documentElement.classList.add('app');
    document.documentElement.setAttribute('data-lcd', '\(lcd)');
    document.documentElement.setAttribute('data-font', '\(font)');
    """
    config.userContentController.addUserScript(
      WKUserScript(source: boot, injectionTime: .atDocumentStart, forMainFrameOnly: true)
    )
    config.preferences.setValue(false, forKey: "developerExtrasEnabled")
    config.preferences.setValue(true, forKey: "allowFileAccessFromFileURLs")
    config.setValue(true, forKey: "allowUniversalAccessFromFileURLs")

    let webView = NoMenuWebView(frame: NSRect(origin: .zero, size: NSSize(width: width, height: height)), configuration: config)
    webView.navigationDelegate = self
    webView.setValue(false, forKey: "drawsBackground")
    if #available(macOS 12.0, *) {
      webView.underPageBackgroundColor = .clear
    }
    webView.allowsMagnification = false
    webView.allowsBackForwardNavigationGestures = false

    guard
      let resourceDir = Bundle.main.resourceURL,
      let html = Bundle.main.url(forResource: "index", withExtension: "html")
    else {
      fatalError("Brak index.html w Resources")
    }
    webView.loadFileURL(html, allowingReadAccessTo: resourceDir)

    webView.autoresizingMask = [.width, .height]
    window.contentView = webView
    window.setContentSize(NSSize(width: width, height: height))
    let mouse = NSEvent.mouseLocation
    let screen = NSScreen.screens.first { NSMouseInRect(mouse, $0.frame, false) } ?? NSScreen.main
    if let vis = screen?.visibleFrame {
      let frameH = height + 28
      window.setFrame(
        NSRect(
          x: vis.midX - width / 2,
          y: vis.midY - frameH / 2,
          width: width,
          height: frameH
        ),
        display: true
      )
    }
    window.makeKeyAndOrderFront(nil)
    window.orderFrontRegardless()
    NSRunningApplication.current.activate(options: [.activateAllWindows, .activateIgnoringOtherApps])
    self.window = window
    self.webView = webView
    refreshChecks()
  }

  func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
    applyTheme()
  }

  func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
    true
  }

  private func applyTheme() {
    let js = "window.CasioCalc && CasioCalc.setTheme('\(lcd)', '\(font)')"
    webView?.evaluateJavaScript(js, completionHandler: nil)
  }

  private func radioItem(title: String, action: Selector, key: String) -> NSMenuItem {
    let item = NSMenuItem(title: title, action: action, keyEquivalent: "")
    item.target = self
    item.representedObject = key
    return item
  }

  private func buildMenu() {
    let menubar = NSMenu()

    let appItem = NSMenuItem()
    menubar.addItem(appItem)
    let appMenu = NSMenu()
    appMenu.addItem(withTitle: "Ukryj CASIO SL-300", action: #selector(NSApplication.hide(_:)), keyEquivalent: "h")
    appMenu.addItem(NSMenuItem.separator())
    appMenu.addItem(withTitle: "Zakończ CASIO SL-300", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
    appItem.submenu = appMenu

    let screenItem = NSMenuItem(title: "Ekran", action: nil, keyEquivalent: "")
    menubar.addItem(screenItem)
    let screenMenu = NSMenu(title: "Ekran")
    let green = radioItem(title: "Zielony", action: #selector(chooseLcd(_:)), key: "green")
    let amber = radioItem(title: "Bursztyn", action: #selector(chooseLcd(_:)), key: "amber")
    let gray = radioItem(title: "Szare LCD (klasyczne)", action: #selector(chooseLcd(_:)), key: "gray")
    screenMenu.addItem(green)
    screenMenu.addItem(amber)
    screenMenu.addItem(gray)
    screenItem.submenu = screenMenu
    lcdItems = ["green": green, "amber": amber, "gray": gray]

    let fontItem = NSMenuItem(title: "Czcionka", action: nil, keyEquivalent: "")
    menubar.addItem(fontItem)
    let fontMenu = NSMenu(title: "Czcionka")
    let modern = radioItem(title: "Obecna", action: #selector(chooseFont(_:)), key: "modern")
    let segment = radioItem(title: "7-segment (lata 80.)", action: #selector(chooseFont(_:)), key: "segment")
    let pixel = radioItem(title: "Pixel LCD (gruby)", action: #selector(chooseFont(_:)), key: "pixel")
    fontMenu.addItem(modern)
    fontMenu.addItem(segment)
    fontMenu.addItem(pixel)
    fontItem.submenu = fontMenu
    fontItems = ["modern": modern, "segment": segment, "pixel": pixel]

    let editItem = NSMenuItem()
    menubar.addItem(editItem)
    let editMenu = NSMenu(title: "Edycja")
    editMenu.addItem(withTitle: "Kopiuj", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
    editItem.submenu = editMenu

    NSApp.mainMenu = menubar
  }

  private func refreshChecks() {
    for (key, item) in lcdItems { item.state = key == lcd ? .on : .off }
    for (key, item) in fontItems { item.state = key == font ? .on : .off }
  }

  @objc func chooseLcd(_ sender: NSMenuItem) {
    guard let key = sender.representedObject as? String else { return }
    lcd = key
    refreshChecks()
    applyTheme()
  }

  @objc func chooseFont(_ sender: NSMenuItem) {
    guard let key = sender.representedObject as? String else { return }
    font = key
    refreshChecks()
    applyTheme()
  }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.run()
