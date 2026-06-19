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
        VStack(spacing: 12) {
            Picker("Image", selection: $showAnnotated) {
                Text("Original").tag(false)
                Text("Annotated").tag(true)
            }
            .pickerStyle(.segmented)
            .padding(.horizontal)

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
            .frame(maxWidth: .infinity, maxHeight: 360)

            if isLoading {
                ProgressView("Rendering")
            }

            if let errorMessage {
                Text(errorMessage)
                    .foregroundStyle(.red)
                    .font(.footnote)
                    .padding(.horizontal)
            }

            if let response {
                List {
                    if !response.warnings.isEmpty {
                        Section("Warnings") {
                            ForEach(response.warnings, id: \.self) { warning in
                                Text(warning)
                            }
                        }
                    }

                    Section("Review") {
                        TextField("Optional notes", text: $reviewNotes, axis: .vertical)
                            .lineLimit(1...4)
                        HStack {
                            Button("Approve") { sendReview("approved") }
                            Button("Reject", role: .destructive) { sendReview("rejected") }
                            Button("Needs Closer Photo") { sendReview("needs_closer_photo") }
                        }
                        if let reviewStatus {
                            Text(reviewStatus)
                                .font(.footnote)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
            }
        }
        .navigationTitle("Result")
        .task {
            await submit()
        }
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
