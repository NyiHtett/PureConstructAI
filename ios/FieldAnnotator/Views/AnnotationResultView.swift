import SwiftUI

struct AnnotationResultView: View {
    let originalImage: UIImage
    let annotationMode: AnnotationMode
    let projectId: String?
    let wallId: String?
    let notes: String?
    let calibrationPayload: CalibrationPayload?

    @State private var client = BackendClient()
    @State private var response: AnnotationResponse?
    @State private var annotatedImage: UIImage?
    @State private var showAnnotated = true
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var reviewNotes = ""
    @State private var reviewStatus: String?

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                viewerPanel

                if isLoading {
                    HStack {
                        ProgressView()
                            .tint(ConstructPalette.safetyOrange)
                        Text("Rendering field reference")
                            .font(.system(size: 14, weight: .bold, design: .monospaced))
                    }
                    .foregroundStyle(ConstructPalette.paper)
                    .constructionPanel()
                }

                if let errorMessage {
                    Text(errorMessage)
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundStyle(.red)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .constructionPanel()
                }

                if let response {
                    warningsPanel(response.warnings)
                    reviewPanel
                }
            }
            .padding(18)
        }
        .constructionBackground()
        .navigationTitle("Result")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            await submit()
        }
    }

    private var viewerPanel: some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionTitle("Rendered Output", symbol: "photo")
            Picker("Image", selection: $showAnnotated) {
                Text("Original").tag(false)
                Text("Annotated").tag(true)
            }
            .pickerStyle(.segmented)

            ZStack {
                RoundedRectangle(cornerRadius: 8)
                    .fill(ConstructPalette.panel)
                    .overlay(BlueprintGrid().clipShape(RoundedRectangle(cornerRadius: 8)))
                    .overlay(RoundedRectangle(cornerRadius: 8).stroke(ConstructPalette.gridLine))

                Group {
                    if showAnnotated, let annotatedImage {
                        Image(uiImage: annotatedImage)
                            .resizable()
                            .scaledToFit()
                    } else {
                        Image(uiImage: originalImage)
                            .resizable()
                            .scaledToFit()
                    }
                }
                .clipShape(RoundedRectangle(cornerRadius: 8))
            }
            .frame(maxWidth: .infinity, minHeight: 260, maxHeight: 380)
        }
        .constructionPanel()
    }

    private func warningsPanel(_ warnings: [String]) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            SectionTitle("Warnings", symbol: "exclamationmark.triangle")
            if warnings.isEmpty {
                Text("No warnings returned.")
                    .foregroundStyle(ConstructPalette.muted)
            } else {
                ForEach(warnings, id: \.self) { warning in
                    Label(warning, systemImage: "exclamationmark.circle")
                        .font(.system(size: 14))
                        .foregroundStyle(ConstructPalette.paper)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
        }
        .constructionPanel()
    }

    private var reviewPanel: some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionTitle("Human Review", symbol: "checkmark.seal")
            TextField("Optional review notes", text: $reviewNotes, axis: .vertical)
                .lineLimit(1...4)
                .textFieldStyle(.plain)
                .padding(12)
                .foregroundStyle(ConstructPalette.paper)
                .background(ConstructPalette.panel, in: RoundedRectangle(cornerRadius: 8))
                .overlay(RoundedRectangle(cornerRadius: 8).stroke(ConstructPalette.gridLine))

            VStack(spacing: 8) {
                Button { sendReview("approved") } label: {
                    Label("Approve", systemImage: "checkmark.seal.fill")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .tint(ConstructPalette.laserGreen)

                Button { sendReview("needs_closer_photo") } label: {
                    Label("Needs Closer Photo", systemImage: "camera.macro")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .tint(ConstructPalette.warning)

                Button(role: .destructive) { sendReview("rejected") } label: {
                    Label("Reject", systemImage: "xmark.seal")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)
            }

            if let reviewStatus {
                Text(reviewStatus.uppercased())
                    .font(.system(size: 12, weight: .bold, design: .monospaced))
                    .foregroundStyle(ConstructPalette.safetyOrange)
            }
        }
        .constructionPanel()
    }

    private func submit() async {
        guard response == nil else { return }
        isLoading = true
        defer { isLoading = false }
        do {
            let created = try await client.submitAnnotation(
                image: originalImage,
                annotationMode: annotationMode,
                projectId: projectId,
                wallId: wallId,
                notes: notes,
                calibrationPayload: calibrationPayload
            )
            response = created
            annotatedImage = try await client.fetchAnnotatedImage(path: created.annotatedImageURL)
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func sendReview(_ eventType: String) {
        guard let response else { return }
        Task {
            do {
                let result = try await client.sendReview(
                    jobId: response.jobId,
                    eventType: eventType,
                    reviewerId: "ios-user",
                    notes: reviewNotes
                )
                reviewStatus = result.status
            } catch {
                errorMessage = error.localizedDescription
            }
        }
    }
}
