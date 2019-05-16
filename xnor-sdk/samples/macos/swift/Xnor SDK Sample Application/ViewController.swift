// Copyright (c) 2019 Xnor.ai, Inc.
//

import AVFoundation
import Cocoa
import XnorNet

class ViewController: NSViewController, AVCaptureVideoDataOutputSampleBufferDelegate {

  var session: AVCaptureSession?
  var device: AVCaptureDevice?
  var previewLayer: AVCaptureVideoPreviewLayer?
  var overlay: InferenceOverlayView?
  var evaluator: XnorModelEvaluator?
  var model: Model?

  override func viewDidLoad() {
    super.viewDidLoad()
    let session = AVCaptureSession()
    session.beginConfiguration()
    let device = AVCaptureDevice.default(for: .video)
    guard
      let videoDeviceInput = try? AVCaptureDeviceInput(device: device!),
      session.canAddInput(videoDeviceInput)
      else { return }
    session.addInput(videoDeviceInput)
    let previewLayer = AVCaptureVideoPreviewLayer(session: session);
    previewLayer.frame = view.bounds;
    previewLayer.autoresizingMask = [.layerWidthSizable, .layerHeightSizable]
    let overlay = InferenceOverlayView()
    overlay.frame = self.view.bounds
    overlay.autoresizingMask = [.width, .height]
    self.view.layer = previewLayer
    self.view.addSubview(overlay)
    guard let model = try? Model(builtIn: nil) else { return }
    let evaluator = XnorModelEvaluator(overlay: overlay, model: model)
    session.addOutput(createAVCaptureOutput(delegate: evaluator))
    session.commitConfiguration()
    session.startRunning()

    self.session = session
    self.device = device
    self.previewLayer = previewLayer
    self.overlay = overlay
    self.evaluator = evaluator
    self.model = model
  }

  override func viewDidAppear() {
    super.viewDidAppear()
    self.view.window?.contentAspectRatio = NSSize(width: 16, height: 9)
  }

  private func createAVCaptureOutput(
    delegate: AVCaptureVideoDataOutputSampleBufferDelegate
    ) -> AVCaptureVideoDataOutput {
    let output = AVCaptureVideoDataOutput()
    output.alwaysDiscardsLateVideoFrames = true
    output.connection(with: .video)?.isEnabled = true
    output.videoSettings = [
      (kCVPixelBufferPixelFormatTypeKey as String): kCVPixelFormatType_24RGB
    ]
    let sampleProcessingDispatchQueue = DispatchQueue(label: "AVCapture Processing",
                                                      attributes: [])
    output.setSampleBufferDelegate(delegate, queue: sampleProcessingDispatchQueue)
    return output
  }
}

