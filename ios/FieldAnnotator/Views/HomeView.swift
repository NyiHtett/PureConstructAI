import SwiftUI

struct HomeView: View {
    @State private var projectId = ""
    @State private var wallId = ""
    @State private var startNewAnnotation = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    header
                    jobPanel
                    pipelinePanel
                    PrimaryConstructButton(title: "Start Site Analysis", symbol: "camera.metering.matrix") {
                        startNewAnnotation = true
                    }
                }
                .padding(18)
            }
            .constructionBackground()
            .navigationTitle("Analyze")
            .navigationBarTitleDisplayMode(.inline)
            .navigationDestination(isPresented: $startNewAnnotation) {
                PhotoCaptureView(projectId: projectId, wallId: wallId)
            }
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("FIELD INTELLIGENCE")
                .font(.system(size: 11, weight: .bold, design: .monospaced))
                .tracking(2.2)
                .foregroundStyle(ConstructPalette.laserGreen)
            Text("Site scan to annotated field reference.")
                .font(.system(size: 34, weight: .heavy, design: .rounded))
                .foregroundStyle(ConstructPalette.paper)
                .lineLimit(2)
                .minimumScaleFactor(0.75)
            Text("Select a job-site photo, choose the analysis mode, capture simple geometry, and receive an OpenCV-rendered construction markup from OpenInfer output.")
                .font(.system(size: 15))
                .foregroundStyle(ConstructPalette.muted)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .constructionPanel()
    }

    private var jobPanel: some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionTitle("Job Context", symbol: "folder")
            TextField("Project ID optional", text: $projectId)
                .textInputAutocapitalization(.never)
                .textFieldStyle(.plain)
                .padding(12)
                .foregroundStyle(ConstructPalette.paper)
                .background(ConstructPalette.panel, in: RoundedRectangle(cornerRadius: 8))
                .overlay(RoundedRectangle(cornerRadius: 8).stroke(ConstructPalette.gridLine))
            TextField("Wall ID optional", text: $wallId)
                .textInputAutocapitalization(.never)
                .textFieldStyle(.plain)
                .padding(12)
                .foregroundStyle(ConstructPalette.paper)
                .background(ConstructPalette.panel, in: RoundedRectangle(cornerRadius: 8))
                .overlay(RoundedRectangle(cornerRadius: 8).stroke(ConstructPalette.gridLine))
        }
        .constructionPanel()
    }

    private var pipelinePanel: some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionTitle("Current Pipeline", symbol: "bolt.horizontal")
            HStack {
                metric("MODEL", "OpenInfer")
                metric("RENDERER", "OpenCV")
            }
            metric("BACKEND", "192.168.1.173:8002")
        }
        .constructionPanel()
    }

    private func metric(_ label: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(label)
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(ConstructPalette.muted)
            Text(value)
                .font(.system(size: 15, weight: .bold, design: .monospaced))
                .foregroundStyle(ConstructPalette.safetyOrange)
                .lineLimit(1)
                .minimumScaleFactor(0.75)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(10)
        .background(ConstructPalette.panel, in: RoundedRectangle(cornerRadius: 7))
        .overlay(RoundedRectangle(cornerRadius: 7).stroke(ConstructPalette.gridLine))
    }
}
