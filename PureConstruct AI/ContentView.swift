import SwiftUI

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

                    Text("Rendered annotations are field markup only. They are not code approval and must be verified before installation.")
                        .foregroundStyle(ConstructPalette.muted)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .constructionPanel()
                }
                .padding(18)
            }
            .constructionBackground()
            .navigationTitle("Field Reference")
            .navigationBarTitleDisplayMode(.inline)
        }
    }

    private func status(_ title: String, _ symbol: String) -> some View {
        Label(title, systemImage: symbol)
            .foregroundStyle(ConstructPalette.paper)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(10)
            .background(ConstructPalette.panel, in: RoundedRectangle(cornerRadius: 7))
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
