import PhotosUI
import SwiftUI

struct PhotoCaptureView: View {
    let projectId: String
    let wallId: String

    @State private var selectedPhoto: PhotosPickerItem?
    @State private var selectedImage: UIImage?
    @State private var annotationMode: AnnotationMode = .electricalLines
    @State private var notes = ""

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                photoPanel
                modePanel
                notesPanel

                if let selectedImage {
                    NavigationLink {
                        GeometryCaptureView(
                            image: selectedImage,
                            annotationMode: annotationMode,
                            projectId: projectId.nilIfBlank,
                            wallId: wallId.nilIfBlank,
                            notes: notes.nilIfBlank
                        )
                    } label: {
                        HStack {
                            Image(systemName: "arrow.right.circle.fill")
                            Text("Continue to Geometry")
                                .fontWeight(.heavy)
                            Spacer()
                        }
                        .font(.system(size: 18, weight: .bold, design: .rounded))
                        .foregroundStyle(ConstructPalette.ink)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 14)
                        .background(ConstructPalette.safetyOrange, in: RoundedRectangle(cornerRadius: 8))
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(18)
        }
        .constructionBackground()
        .navigationTitle("Site Analysis")
        .navigationBarTitleDisplayMode(.inline)
        .task(id: selectedPhoto) {
            guard let selectedPhoto else { return }
            if let data = try? await selectedPhoto.loadTransferable(type: Data.self) {
                selectedImage = UIImage(data: data)
            }
        }
        // TODO: Add camera capture source beside PhotosPicker in the next device-capture phase.
    }

    private var photoPanel: some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionTitle("Job-Site Image", symbol: "viewfinder")
            PhotosPicker(selection: $selectedPhoto, matching: .images) {
                ZStack {
                    RoundedRectangle(cornerRadius: 8)
                        .fill(ConstructPalette.panel.opacity(0.9))
                        .overlay(BlueprintGrid().clipShape(RoundedRectangle(cornerRadius: 8)))
                        .overlay(RoundedRectangle(cornerRadius: 8).stroke(ConstructPalette.gridLine))

                    if let selectedImage {
                        Image(uiImage: selectedImage)
                            .resizable()
                            .scaledToFill()
                            .frame(height: 260)
                            .clipShape(RoundedRectangle(cornerRadius: 8))
                            .overlay(alignment: .bottomLeading) {
                                Label("Image staged", systemImage: "checkmark.seal.fill")
                                    .font(.system(size: 12, weight: .bold, design: .monospaced))
                                    .foregroundStyle(ConstructPalette.ink)
                                    .padding(.horizontal, 10)
                                    .padding(.vertical, 7)
                                    .background(ConstructPalette.laserGreen, in: Capsule())
                                    .padding(12)
                            }
                    } else {
                        VStack(spacing: 12) {
                            Image(systemName: "camera.aperture")
                                .font(.system(size: 42, weight: .light))
                                .foregroundStyle(ConstructPalette.safetyOrange)
                            Text("Tap to stage a site image")
                                .font(.system(size: 24, weight: .heavy, design: .rounded))
                                .foregroundStyle(ConstructPalette.paper)
                            Text("Framing, utilities, floor plane, or field condition.")
                                .font(.system(size: 13))
                                .foregroundStyle(ConstructPalette.muted)
                                .multilineTextAlignment(.center)
                        }
                        .padding(24)
                    }
                }
                .frame(height: 260)
            }
            .buttonStyle(.plain)
        }
        .constructionPanel()
    }

    private var modePanel: some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionTitle("Annotation Mode", symbol: "slider.horizontal.3")
            Picker("Annotation Mode", selection: $annotationMode) {
                ForEach(AnnotationMode.allCases) { mode in
                    Text(mode.title).tag(mode)
                }
            }
            .pickerStyle(.menu)
            .tint(ConstructPalette.safetyOrange)
            .padding(12)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(ConstructPalette.panel, in: RoundedRectangle(cornerRadius: 8))
            .overlay(RoundedRectangle(cornerRadius: 8).stroke(ConstructPalette.gridLine))
        }
        .constructionPanel()
    }

    private var notesPanel: some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionTitle("Field Notes", symbol: "note.text")
            TextField("Optional field notes", text: $notes, axis: .vertical)
                .lineLimit(2...5)
                .textFieldStyle(.plain)
                .padding(12)
                .foregroundStyle(ConstructPalette.paper)
                .background(ConstructPalette.panel, in: RoundedRectangle(cornerRadius: 8))
                .overlay(RoundedRectangle(cornerRadius: 8).stroke(ConstructPalette.gridLine))
        }
        .constructionPanel()
    }
}

private extension String {
    var nilIfBlank: String? {
        let trimmed = trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? nil : trimmed
    }
}
