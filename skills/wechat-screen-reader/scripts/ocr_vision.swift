import Foundation
import Vision
import AppKit

if CommandLine.arguments.count < 2 {
    fputs("usage: ocr_vision <image_path>\n", stderr)
    exit(2)
}

let imagePath = CommandLine.arguments[1]
let imageURL = URL(fileURLWithPath: imagePath)

guard let nsImage = NSImage(contentsOf: imageURL),
      let cgImage = nsImage.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    fputs("failed to load image: \(imagePath)\n", stderr)
    exit(1)
}

let request = VNRecognizeTextRequest { request, error in
    if let error = error {
        fputs("ocr error: \(error)\n", stderr)
        exit(1)
    }

    let observations = (request.results as? [VNRecognizedTextObservation]) ?? []
    let rows = observations.compactMap { observation -> [String: Any]? in
        guard let candidate = observation.topCandidates(1).first else { return nil }
        let box = observation.boundingBox
        return [
            "text": candidate.string,
            "confidence": candidate.confidence,
            "x": box.origin.x,
            "y": box.origin.y,
            "w": box.width,
            "h": box.height
        ]
    }

    let data = try! JSONSerialization.data(withJSONObject: rows, options: [.prettyPrinted, .sortedKeys])
    FileHandle.standardOutput.write(data)
}

request.recognitionLevel = .accurate
request.usesLanguageCorrection = true
request.recognitionLanguages = ["zh-Hans", "zh-Hant", "en-US"]

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
try handler.perform([request])
