import SwiftUI

struct HomeView: View {
    @State private var projectId = ""
    @State private var wallId = ""
    @State private var startNewAnnotation = false

    var body: some View {
        NavigationStack {
            Form {
                Section("Job") {
                    TextField("Project ID optional", text: $projectId)
                        .textInputAutocapitalization(.never)
                    TextField("Wall ID optional", text: $wallId)
                        .textInputAutocapitalization(.never)
                }

                Section {
                    Button {
                        startNewAnnotation = true
                    } label: {
                        Label("New Annotation", systemImage: "plus.viewfinder")
                            .frame(maxWidth: .infinity, alignment: .center)
                    }
                }
            }
            .navigationTitle("FieldAnnotator")
            .navigationDestination(isPresented: $startNewAnnotation) {
                PhotoCaptureView(projectId: projectId, wallId: wallId)
            }
        }
    }
}
