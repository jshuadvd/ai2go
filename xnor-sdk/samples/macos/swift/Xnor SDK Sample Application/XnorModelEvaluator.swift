// Copyright (c) 2019 Xnor.ai, Inc.
//

import AVFoundation
import XnorNet

enum XnorModelEvaluatorError: Error {
  case invalidInputImageFormat
  case unknownEvaluationResultType
}

class XnorModelEvaluator: NSObject, AVCaptureVideoDataOutputSampleBufferDelegate {
  
  let overlay: InferenceOverlayView
  let model: Model

  init(overlay: InferenceOverlayView, model: Model) {
    self.overlay = overlay
    self.model = model
  }

  private func newInput(image: CVImageBuffer) throws -> Input {
    // Convert image to xnornet Input
    let pixelFormat = CVPixelBufferGetPixelFormatType(image)
    if pixelFormat != kCVPixelFormatType_24RGB {
      throw XnorModelEvaluatorError.invalidInputImageFormat
    }
    CVPixelBufferLockBaseAddress(image, []);
    let baseAddress: UnsafeMutableRawPointer? = CVPixelBufferGetBaseAddress(image);
    let bytesPerRow = CVPixelBufferGetBytesPerRow(image);
    let width = CVPixelBufferGetWidth(image);
    let height = CVPixelBufferGetHeight(image);
    // xnornet does not handle images with stride larger than a row
    if bytesPerRow != 3 * width {
      throw XnorModelEvaluatorError.invalidInputImageFormat
    }
    let data: Data = Data(bytes: baseAddress!, count: bytesPerRow * height)
    CVPixelBufferUnlockBaseAddress(image, [])
    return try Input(fromRgbImage: data, width: width, height: height)
  }

  private func evaluateModel(input: Input) throws {
    let results = try model.evaluate(input: input)
    overlay.clearOverlays()
    switch results {
      case let boundingBoxes as BoundingBoxes:
        for result in boundingBoxes.value {
          overlay.addOverlay(BoundingBoxOverlay(bounding_box: result))
        }
      case let classLabels as ClassLabels:
        for (i, result) in classLabels.value.enumerated() {
            overlay.addOverlay(TextOverlay(classLabel: result, index: i))
        }
      default:
        throw XnorModelEvaluatorError.unknownEvaluationResultType
    }
    DispatchQueue.main.async {
      self.overlay.setNeedsDisplay(self.overlay.bounds)
    }
  }

  func captureOutput(_ output: AVCaptureOutput,
                     didOutput sampleBuffer: CMSampleBuffer,
                     from connection: AVCaptureConnection) {
    do {
      let image: CVImageBuffer = CMSampleBufferGetImageBuffer(sampleBuffer)!
      let input: Input = try newInput(image: image)
      try evaluateModel(input: input)
    } catch {
      print("Error processing video frame: \(error)")
    }
  }
}
