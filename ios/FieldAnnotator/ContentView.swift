import SwiftUI
import UIKit

struct ContentView: View {
    var body: some View {
        TabView {
            HomeView()
                .tabItem {
                    Label("Analyze", systemImage: "camera.metering.matrix")
                }

            FieldReferenceView()
                .tabItem {
                    Label("Reports", systemImage: "doc.text.magnifyingglass")
                }

            InventoryPlaceholderView()
                .tabItem {
                    Label("Inventory", systemImage: "shippingbox")
                }
        }
    }
}

private struct FieldReferenceView: View {
    @State private var client = BackendClient()
    @State private var approvedReferences: [ApprovedFieldReference] = []
    @State private var rejectedReferences: [RejectedFieldReference] = []
    @State private var images: [String: UIImage] = [:]
    @State private var isLoading = false
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    VStack(alignment: .leading, spacing: 10) {
                        SectionTitle("Review Statuses", symbol: "checklist")
                        status("Rendered", "photo")
                        status("Approved for Field Reference", "checkmark.seal")
                        status("Rejected", "xmark.seal")
                        status("Needs Closer Photo", "camera.macro")
                    }
                    .constructionPanel()

                    VStack(alignment: .leading, spacing: 12) {
                        SectionTitle("Approved for Field Reference", symbol: "checkmark.seal")

                        if isLoading {
                            loadingRow("Loading approved references")
                        } else if let errorMessage {
                            errorRow(errorMessage)
                        } else if approvedReferences.isEmpty {
                            Text("No approved field references yet.")
                                .foregroundStyle(ConstructPalette.muted)
                        } else {
                            ForEach(approvedReferences) { reference in
                                approvedReferenceCard(reference)
                            }
                        }
                    }
                    .constructionPanel()

                    VStack(alignment: .leading, spacing: 12) {
                        SectionTitle("Rejected", symbol: "xmark.seal")

                        if isLoading {
                            loadingRow("Loading rejected references")
                        } else if let errorMessage {
                            errorRow(errorMessage)
                        } else if rejectedReferences.isEmpty {
                            Text("No rejected references yet.")
                                .foregroundStyle(ConstructPalette.muted)
                        } else {
                            ForEach(rejectedReferences) { reference in
                                rejectedReferenceCard(reference)
                            }
                        }
                    }
                    .constructionPanel()
                }
                .padding(18)
            }
            .constructionBackground()
            .navigationTitle("Field Reference")
            .navigationBarTitleDisplayMode(.inline)
            .task {
                await loadFieldReferences()
            }
            .refreshable {
                await loadFieldReferences()
            }
        }
    }

    private func status(_ title: String, _ symbol: String) -> some View {
        Label(title, systemImage: symbol)
            .foregroundStyle(ConstructPalette.paper)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(10)
            .background(ConstructPalette.panel, in: RoundedRectangle(cornerRadius: 7))
    }

    private func loadingRow(_ title: String) -> some View {
        HStack {
            ProgressView()
                .tint(ConstructPalette.safetyOrange)
            Text(title)
                .font(.system(size: 14, weight: .bold, design: .monospaced))
        }
        .foregroundStyle(ConstructPalette.paper)
    }

    private func errorRow(_ message: String) -> some View {
        Text(message)
            .font(.system(size: 13, weight: .semibold))
            .foregroundStyle(.red)
    }

    private func approvedReferenceCard(_ reference: ApprovedFieldReference) -> some View {
        referenceCard(
            imageKey: "approved-\(reference.id)",
            annotationMode: reference.annotationMode,
            projectId: reference.projectId,
            wallId: reference.wallId,
            notes: reference.notes
        )
    }

    private func rejectedReferenceCard(_ reference: RejectedFieldReference) -> some View {
        referenceCard(
            imageKey: "rejected-\(reference.id)",
            annotationMode: reference.annotationMode,
            projectId: reference.projectId,
            wallId: reference.wallId,
            notes: reference.notes
        )
    }

    private func referenceCard(
        imageKey: String,
        annotationMode: AnnotationMode,
        projectId: String?,
        wallId: String?,
        notes: String?
    ) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            ZStack {
                RoundedRectangle(cornerRadius: 8)
                    .fill(ConstructPalette.panel)
                    .overlay(BlueprintGrid().clipShape(RoundedRectangle(cornerRadius: 8)))
                    .overlay(RoundedRectangle(cornerRadius: 8).stroke(ConstructPalette.gridLine))

                if let image = images[imageKey] {
                    Image(uiImage: image)
                        .resizable()
                        .scaledToFit()
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                } else {
                    ProgressView()
                        .tint(ConstructPalette.safetyOrange)
                }
            }
            .frame(maxWidth: .infinity, minHeight: 180, maxHeight: 280)

            Text(annotationMode.title)
                .font(.system(size: 16, weight: .heavy, design: .rounded))
                .foregroundStyle(ConstructPalette.paper)

            HStack {
                Label(projectId ?? "No project", systemImage: "folder")
                Label(wallId ?? "No wall", systemImage: "rectangle.dashed")
            }
            .font(.system(size: 12, weight: .bold, design: .monospaced))
            .foregroundStyle(ConstructPalette.muted)

            if let notes, !notes.isEmpty {
                Text(notes)
                    .font(.system(size: 13))
                    .foregroundStyle(ConstructPalette.muted)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
        .padding(10)
        .background(ConstructPalette.panel, in: RoundedRectangle(cornerRadius: 8))
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(ConstructPalette.gridLine))
    }

    private func loadFieldReferences() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            let loadedApprovedReferences = try await client.fetchApprovedFieldReferences()
            let loadedRejectedReferences = try await client.fetchRejectedFieldReferences()
            approvedReferences = loadedApprovedReferences
            rejectedReferences = loadedRejectedReferences

            for reference in loadedApprovedReferences where images["approved-\(reference.id)"] == nil {
                images["approved-\(reference.id)"] = try await client.fetchAnnotatedImage(path: reference.imageURL)
            }
            for reference in loadedRejectedReferences where images["rejected-\(reference.id)"] == nil {
                images["rejected-\(reference.id)"] = try await client.fetchAnnotatedImage(path: reference.imageURL)
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

private struct InventoryPlaceholderView: View {
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
                    SectionTitle("Inventory", symbol: "shippingbox")
                    Label("Material matching will live here.", systemImage: "shippingbox")
                    Label("Annotation now runs from Analyze.", systemImage: "viewfinder")
                }
                .foregroundStyle(ConstructPalette.paper)
                .constructionPanel()
                .padding(18)
            }
            .constructionBackground()
            .navigationTitle("Inventory")
            .navigationBarTitleDisplayMode(.inline)
        }
    }
}
