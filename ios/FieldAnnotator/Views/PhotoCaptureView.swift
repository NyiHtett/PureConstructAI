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
        Form {
            Section("Photo") {
                PhotosPicker(selection: $selectedPhoto, matching: .images) {
                    Label(selectedImage == nil ? "Choose Photo" : "Replace Photo", systemImage: "photo")
                }

                if let selectedImage {
                    Image(uiImage: selectedImage)
                        .resizable()
                        .scaledToFit()
                        .frame(maxHeight: 280)
                }
            }

            Section("Mode") {
                AnnotationModePickerView(selection: $annotationMode)
            }

            Section("Notes") {
                TextField("Optional field notes", text: $notes, axis: .vertical)
                    .lineLimit(2...5)
            }

            Section {
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
                        Label("Continue", systemImage: "arrow.right")
                    }
                }
            }
        }
        .navigationTitle("New Annotation")
        .task(id: selectedPhoto) {
            guard let selectedPhoto else { return }
            if let data = try? await selectedPhoto.loadTransferable(type: Data.self) {
                selectedImage = UIImage(data: data)
            }
        }
        // TODO: Add camera capture source beside PhotosPicker in the next device-capture phase.
    }
}

private extension String {
    var nilIfBlank: String? {
        let trimmed = trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? nil : trimmed
    }
}
