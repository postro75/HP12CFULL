import Cocoa
import WebKit

final class NoMenuWebView: WKWebView {
  override func willOpenMenu(_ menu: NSMenu, with event: NSEvent) {
    menu.removeAllItems()
  }
}

final class AppDelegate: NSObject, NSApplicationDelegate, WKNavigationDelegate {
  var window: NSWindow?

  func applicationDidFinishLaunching(_ notification: Notification) {
    let width: CGFloat = 430
    let height: CGFloat = 760
    let window = NSWindow(
      contentRect: NSRect(x: 0, y: 0, width: width, height: height),
      styleMask: [.titled, .closable, .miniaturizable],
      backing: .buffered,
      defer: false
    )
    window.title = "CASIO SL-300"
    window.isMovableByWindowBackground = true
    window.backgroundColor = NSColor(calibratedWhite: 0.03, alpha: 1)
    window.collectionBehavior = [.moveToActiveSpace, .fullScreenNone]
    window.isReleasedWhenClosed = false
    window.tabbingMode = .disallowed

    let config = WKWebViewConfiguration()
    let script = WKUserScript(
      source: "document.documentElement.classList.add('app');",
      injectionTime: .atDocumentStart,
      forMainFrameOnly: true
    )
    config.userContentController.addUserScript(script)
    config.preferences.setValue(false, forKey: "developerExtrasEnabled")

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
    if let screen = NSScreen.main {
      let vis = screen.visibleFrame
      let frame = NSRect(
        x: vis.midX - width / 2,
        y: vis.midY - height / 2,
        width: width,
        height: height + 28
      )
      window.setFrame(frame, display: true)
    }
    window.makeKeyAndOrderFront(nil)
    window.orderFrontRegardless()
    NSRunningApplication.current.activate(options: [.activateAllWindows, .activateIgnoringOtherApps])
    self.window = window
  }

  func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
    true
  }
}

func buildMenu() {
  let menubar = NSMenu()
  let appItem = NSMenuItem()
  menubar.addItem(appItem)
  let appMenu = NSMenu()
  appMenu.addItem(withTitle: "Ukryj CASIO SL-300", action: #selector(NSApplication.hide(_:)), keyEquivalent: "h")
  appMenu.addItem(NSMenuItem.separator())
  appMenu.addItem(withTitle: "Zakończ CASIO SL-300", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
  appItem.submenu = appMenu

  let editItem = NSMenuItem()
  menubar.addItem(editItem)
  let editMenu = NSMenu(title: "Edycja")
  editMenu.addItem(withTitle: "Kopiuj", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
  editItem.submenu = editMenu
  NSApp.mainMenu = menubar
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.setActivationPolicy(.regular)
buildMenu()
app.run()
