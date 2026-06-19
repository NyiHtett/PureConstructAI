import SwiftUI

struct ContentView: View {
    var body: some View {
        TabView {
            PureConstructDashboardView()
                .tabItem {
                    Label("Home", systemImage: "house")
                }

            HomeView()
                .tabItem {
                    Label("Annotate", systemImage: "viewfinder")
                }

            FieldReferenceView()
                .tabItem {
                    Label("Field Ref", systemImage: "checklist")
                }
        }
    }
}

private struct PureConstructDashboardView: View {
    @State private var showAnnotation = false

    var body: some View {
        NavigationStack {
            List {
                Section {
                    VStack(alignment: .leading, spacing: 10) {
                        Text("PureConstruct AI")
                            .font(.largeTitle.bold())
                        Text("Construction field tools for photo annotation, review, and crew communication.")
                            .foregroundStyle(.secondary)
                    }
                    .padding(.vertical, 8)
                }

                Section("Tools") {
                    NavigationLink {
                        HomeView()
                    } label: {
                        Label("Field Photo Annotation", systemImage: "viewfinder.rectangular")
                    }

                    Label("Inventory and reports can remain here as separate modules.", systemImage: "shippingbox")
                        .foregroundStyle(.secondary)
                }

                Section("Current Backend") {
                    LabeledContent("Server", value: "192.168.1.173:8002")
                    LabeledContent("Model", value: "OpenInfer")
                    LabeledContent("Renderer", value: "OpenCV")
                }
            }
            .navigationTitle("PureConstruct")
        }
    }
}

private struct FieldReferenceView: View {
    var body: some View {
        NavigationStack {
            List {
                Section("Review Statuses") {
                    Label("Rendered", systemImage: "photo")
                    Label("Approved for Field Reference", systemImage: "checkmark.seal")
                    Label("Rejected", systemImage: "xmark.seal")
                    Label("Needs Closer Photo", systemImage: "camera.macro")
                }

                Section("Field Use") {
                    Text("Rendered annotations are field markup only. They are not code approval and must be verified before installation.")
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Field Reference")
        }
    }
}
