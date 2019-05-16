// Copyright (c) 2019 Xnor.ai, Inc.
//

import Cocoa

/// An NSView that draws zero or more overlays conforming to the InferenceOverlay protocol
class InferenceOverlayView: NSView {
  var overlays: [InferenceOverlay] = []
  
  func addOverlay(_ overlay: InferenceOverlay) {
    overlays.append(overlay)
  }
  
  func clearOverlays() {
    overlays = []
  }
  
  override func draw(_ dirtyRect: NSRect) {
    super.draw(dirtyRect)
    if let context: CGContext = NSGraphicsContext.current?.cgContext {
      for overlay in overlays {
        overlay.draw(context: context)
      }
    }
  }
}
