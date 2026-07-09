import Foundation
import CoreGraphics

if CommandLine.arguments.count < 4 {
    fputs("usage: scroll_at <x> <y> <deltaY>\n", stderr)
    exit(2)
}

let x = Double(CommandLine.arguments[1])!
let y = Double(CommandLine.arguments[2])!
let deltaY = Int32(CommandLine.arguments[3])!

let point = CGPoint(x: x, y: y)
let move = CGEvent(mouseEventSource: nil, mouseType: .mouseMoved, mouseCursorPosition: point, mouseButton: .left)
move?.post(tap: .cghidEventTap)
usleep(80_000)

let scroll = CGEvent(scrollWheelEvent2Source: nil, units: .pixel, wheelCount: 2, wheel1: deltaY, wheel2: 0, wheel3: 0)
scroll?.post(tap: .cghidEventTap)
usleep(80_000)
