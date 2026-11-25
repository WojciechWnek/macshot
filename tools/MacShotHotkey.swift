import Carbon
import Foundation

// Global hotkey listener for MacShot.
//
// It registers Control+Shift+4 system-wide with Carbon's RegisterEventHotKey
// (no Accessibility permission needed), and runs MACSHOT_CAPTURE when pressed.
//
// To change the shortcut, edit the two constants below and run
// bin/install-hotkey again.

private let hotKeyModifiers = UInt32(controlKey | shiftKey)
private let hotKeyKeyCode = UInt32(kVK_ANSI_4) // 4 on a US keyboard

private func log(_ message: String) {
    let line = "MacShotHotkey: \(message)\n"
    FileHandle.standardError.write(Data(line.utf8))
}

private func runCapture() {
    let environment = ProcessInfo.processInfo.environment
    guard let path = environment["MACSHOT_CAPTURE"], !path.isEmpty else {
        log("MACSHOT_CAPTURE is not set")
        return
    }

    let process = Process()
    process.executableURL = URL(fileURLWithPath: path)
    process.arguments = []
    process.environment = environment

    do {
        try process.run()
    } catch {
        log("failed to start capture: \(error)")
    }
}

private func handleHotKey(
    _ callRef: EventHandlerCallRef?,
    _ event: EventRef?,
    _ userData: UnsafeMutableRawPointer?
) -> OSStatus {
    log("hotkey pressed")
    runCapture()
    return noErr
}

private func installHotKey() -> Bool {
    var eventType = EventTypeSpec(
        eventClass: OSType(kEventClassKeyboard),
        eventKind: UInt32(kEventHotKeyPressed)
    )

    var handlerRef: EventHandlerRef?
    let installStatus = InstallEventHandler(
        GetApplicationEventTarget(),
        handleHotKey,
        1,
        &eventType,
        nil,
        &handlerRef
    )
    guard installStatus == noErr else {
        log("InstallEventHandler failed: \(installStatus)")
        return false
    }

    var hotKeyRef: EventHotKeyRef?
    let hotKeyID = EventHotKeyID(signature: OSType(0x4D534854), id: 1) // 'MSHT'
    let registerStatus = RegisterEventHotKey(
        hotKeyKeyCode,
        hotKeyModifiers,
        hotKeyID,
        GetApplicationEventTarget(),
        0,
        &hotKeyRef
    )
    guard registerStatus == noErr else {
        log("RegisterEventHotKey failed: \(registerStatus) — shortcut may be in use")
        return false
    }

    return true
}

// Carbon's application event loop is marked 32-bit-only in the public headers,
// but the symbol is still exported on 64-bit and is used by tools such as
// SketchyBar. RunCurrentEventLoop does not dispatch application-target hotkey
// events in a bare CLI, so bind the real application loop directly.
@_silgen_name("RunApplicationEventLoop")
private func runApplicationEventLoop()

if !installHotKey() {
    exit(1)
}

log("registered Control+Shift+4")
runApplicationEventLoop()
