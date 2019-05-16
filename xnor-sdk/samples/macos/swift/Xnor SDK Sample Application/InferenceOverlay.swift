// Copyright (c) 2019 Xnor.ai, Inc.
//

import Foundation
import XnorNet

protocol InferenceOverlay {
  func draw(context: CGContext)
}

struct TextOverlay: InferenceOverlay {
  static let lineWidth: CGFloat = BoundingBoxOverlay.lineWidth
  static let textSize: CGFloat = lineWidth * 3

  let text: String
  let bgColor: CGColor
  let textColor: CGColor
  let x: CGFloat
  let y: CGFloat

  init(classLabel: ClassLabel, index: Int = 0) {
    self.text = classLabel.label
    self.bgColor = SampleColors.sampleColor(index: classLabel.classId)
    self.textColor = CGColor.black
    self.x = 0
    self.y = (2 * TextOverlay.lineWidth + TextOverlay.textSize) * CGFloat(index + 1)
  }

  init(text: String, x: CGFloat = 0, y: CGFloat = 0, bgColor: CGColor = CGColor.black) {
    self.text = text
    self.bgColor = bgColor
    self.textColor = CGColor.black
    self.x = x
    self.y = y
  }

  func draw(context: CGContext) {
    let bigEnough = CGSize(width: 800, height: 100)
    let font = CTFontCreateUIFontForLanguage(.label, TextOverlay.textSize, nil)
    let tightBounds = (text as NSString).boundingRect(
      with: bigEnough,
      options: [],
      attributes: [.font: font as Any]
    )
    // Draw background for label
    var bgBounds = tightBounds.offsetBy(dx: self.x,
                                        dy: self.y - tightBounds.height + TextOverlay.lineWidth)
    bgBounds = bgBounds.insetBy(dx: -TextOverlay.lineWidth / 2, dy: 0)
    context.setFillColor(self.bgColor)
    context.fill(bgBounds)
    // Draw label text
    var textBounds = bgBounds.offsetBy(dx: 0, dy: tightBounds.height / 4)
    textBounds = textBounds.insetBy(dx: TextOverlay.lineWidth / 2, dy: 0)
    text.draw(
      with: textBounds,
      options: [],
      attributes: [.font: font as Any],
      context: nil
    )
  }
}

struct BoundingBoxOverlay: InferenceOverlay {
  static let lineWidth: CGFloat = 8

  let bounds: Rectangle
  let text: String
  let color: CGColor

  init(bounding_box: BoundingBox) {
    self.bounds = bounding_box.rectangle
    self.color = SampleColors.sampleColor(index: bounding_box.classLabel.classId)
    self.text = bounding_box.classLabel.label
  }

  func draw(context: CGContext) {
    let x = CGFloat(self.bounds.x) * CGFloat(context.width)
    let y = CGFloat(self.bounds.y) * CGFloat(context.height)
    let width = CGFloat(self.bounds.width) * CGFloat(context.width) - BoundingBoxOverlay.lineWidth
    let height = CGFloat(self.bounds.height) * CGFloat(context.height)
                 - BoundingBoxOverlay.lineWidth

    context.setStrokeColor(self.color)
    let boundingBox = context.convertToUserSpace(CGRect(x: x, y: y, width: width, height: height))
    context.stroke(boundingBox, width: BoundingBoxOverlay.lineWidth)
    let label = TextOverlay(text: self.text, x: boundingBox.minX,
                            y: boundingBox.minY + boundingBox.maxY,
                            bgColor: self.color)
    label.draw(context: context)
  }
}
