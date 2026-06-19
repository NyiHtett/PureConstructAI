import SwiftUI

struct GeometryCaptureView: View {
    let image: UIImage
    let annotationMode: AnnotationMode
    let projectId: String?
    let wallId: String?
    let notes: String?

    @State private var wallCorners: [NormalizedPoint] = []
    @State private var floorCorners: [NormalizedPoint] = []
    @State private var studCenterlines: [StudCenterline] = []
    @State private var pendingStudTop: NormalizedPoint?
    @State private var calibrationPayload: CalibrationPayload?
    @State private var submitNow = false

    var body: some View {
        VStack(spacing: 14) {
            VStack(alignment: .leading, spacing: 10) {
                SectionTitle("Geometry Capture", symbol: "point.3.connected.trianglepath.dotted")
                Text(instruction)
                    .font(.system(size: 18, weight: .bold, design: .rounded))
                    .foregroundStyle(ConstructPalette.paper)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .constructionPanel()
            .padding(.horizontal, 18)
            .padding(.top, 14)

            ZStack {
                RoundedRectangle(cornerRadius: 8)
                    .fill(ConstructPalette.panel)
                    .overlay(BlueprintGrid().clipShape(RoundedRectangle(cornerRadius: 8)))
                    .overlay(RoundedRectangle(cornerRadius: 8).stroke(ConstructPalette.gridLine))

                GeometryReader { proxy in
                    let displaySize = displayedImageSize(in: proxy.size)
                    ZStack {
                        Image(uiImage: image)
                            .resizable()
                            .scaledToFit()
                            .frame(width: proxy.size.width, height: proxy.size.height)

                        GeometryOverlayView(
                            wallCorners: wallCorners,
                            studCenterlines: studCenterlines,
                            floorCorners: floorCorners,
                            currentStudTop: pendingStudTop
                        )
                        .frame(width: displaySize.width, height: displaySize.height)
                        .position(x: proxy.size.width / 2, y: proxy.size.height / 2)
                    }
                    .contentShape(Rectangle())
                    .gesture(
                        DragGesture(minimumDistance: 0)
                            .onEnded { value in
                                handleTap(value.location, containerSize: proxy.size)
                            }
                    )
                }
            }
            .frame(minHeight: 320)
            .padding(.horizontal, 18)

            HStack {
                Button {
                    undoLast()
                } label: {
                    Label("Undo", systemImage: "arrow.uturn.backward")
                }
                    .disabled(!canUndo)
                Button {
                    reset()
                } label: {
                    Label("Reset", systemImage: "xmark.circle")
                }
                Spacer()
                Button(annotationMode == .fieldNotes ? "Skip" : "Done") {
                    calibrationPayload = buildPayload()
                    submitNow = true
                }
                .buttonStyle(.borderedProminent)
                .tint(ConstructPalette.safetyOrange)
            }
            .padding(.horizontal)
            .foregroundStyle(ConstructPalette.paper)
        }
        .constructionBackground()
        .navigationTitle("Geometry")
        .navigationBarTitleDisplayMode(.inline)
        .navigationDestination(isPresented: $submitNow) {
            AnnotationResultView(
                originalImage: image,
                annotationMode: annotationMode,
                projectId: projectId,
                wallId: wallId,
                notes: notes,
                calibrationPayload: calibrationPayload
            )
        }
        // TODO: Add guided camera overlays and persisted reusable wall calibration in GeometryCaptureView phase 2.
    }

    private var instruction: String {
        switch annotationMode {
        case .electricalLines, .studLocations:
            if wallCorners.count < 4 {
                return ["Tap wall top-left", "Tap wall top-right", "Tap wall bottom-right", "Tap wall bottom-left"][wallCorners.count]
            }
            return pendingStudTop == nil ? "Tap top of stud center, or Done" : "Tap bottom of stud center"
        case .flooringPattern:
            if floorCorners.count < 4 {
                return ["Tap floor front-left", "Tap floor front-right", "Tap floor back-right", "Tap floor back-left"][floorCorners.count]
            }
            return "Tap Done"
        case .fieldNotes:
            return "Geometry optional"
        }
    }

    private var canUndo: Bool {
        !wallCorners.isEmpty || !floorCorners.isEmpty || !studCenterlines.isEmpty || pendingStudTop != nil
    }

    private func handleTap(_ location: CGPoint, containerSize: CGSize) {
        guard let point = GeometryNormalizer.normalizedPoint(
            tapLocation: location,
            imageSize: image.size,
            containerSize: containerSize
        ) else { return }

        switch annotationMode {
        case .electricalLines, .studLocations:
            if wallCorners.count < 4 {
                wallCorners.append(NormalizedPoint(x: point.x, y: point.y, label: wallCornerLabel(wallCorners.count)))
            } else if let top = pendingStudTop {
                studCenterlines.append(StudCenterline(id: "S\(studCenterlines.count + 1)", top: top, bottom: point))
                pendingStudTop = nil
            } else {
                pendingStudTop = point
            }
        case .flooringPattern:
            if floorCorners.count < 4 {
                floorCorners.append(NormalizedPoint(x: point.x, y: point.y, label: floorCornerLabel(floorCorners.count)))
            }
        case .fieldNotes:
            break
        }
    }

    private func undoLast() {
        if pendingStudTop != nil {
            pendingStudTop = nil
        } else if !studCenterlines.isEmpty {
            studCenterlines.removeLast()
        } else if !floorCorners.isEmpty {
            floorCorners.removeLast()
        } else if !wallCorners.isEmpty {
            wallCorners.removeLast()
        }
    }

    private func reset() {
        wallCorners = []
        floorCorners = []
        studCenterlines = []
        pendingStudTop = nil
    }

    private func buildPayload() -> CalibrationPayload {
        CalibrationPayload(
            imageWidth: Int(image.size.width),
            imageHeight: Int(image.size.height),
            wallCornersNorm: wallCorners,
            studCenterlinesNorm: studCenterlines,
            floorPlaneNorm: floorCorners.count == 4 ? FloorPlane(corners: floorCorners) : nil,
            createdAt: Date()
        )
    }

    private func displayedImageSize(in container: CGSize) -> CGSize {
        let scale = min(container.width / image.size.width, container.height / image.size.height)
        return CGSize(width: image.size.width * scale, height: image.size.height * scale)
    }

    private func wallCornerLabel(_ index: Int) -> String {
        ["top_left", "top_right", "bottom_right", "bottom_left"][index]
    }

    private func floorCornerLabel(_ index: Int) -> String {
        ["front_left", "front_right", "back_right", "back_left"][index]
    }
}
