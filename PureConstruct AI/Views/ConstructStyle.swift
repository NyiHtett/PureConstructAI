import SwiftUI

enum ConstructPalette {
    static let ink = Color(red: 0.06, green: 0.07, blue: 0.07)
    static let paper = Color(red: 0.94, green: 0.93, blue: 0.88)
    static let muted = Color(red: 0.65, green: 0.68, blue: 0.66)
    static let panel = Color(red: 0.10, green: 0.12, blue: 0.12)
    static let card = Color(red: 0.14, green: 0.16, blue: 0.15)
    static let gridLine = Color.white.opacity(0.08)
    static let safetyOrange = Color(red: 1.00, green: 0.47, blue: 0.12)
    static let laserGreen = Color(red: 0.54, green: 0.95, blue: 0.42)
    static let warning = Color(red: 1.00, green: 0.78, blue: 0.22)
}

struct BlueprintGrid: View {
    var body: some View {
        Canvas { context, size in
            let spacing: CGFloat = 26
            var path = Path()
            var x: CGFloat = 0
            while x <= size.width {
                path.move(to: CGPoint(x: x, y: 0))
                path.addLine(to: CGPoint(x: x, y: size.height))
                x += spacing
            }
            var y: CGFloat = 0
            while y <= size.height {
                path.move(to: CGPoint(x: 0, y: y))
                path.addLine(to: CGPoint(x: size.width, y: y))
                y += spacing
            }
            context.stroke(path, with: .color(ConstructPalette.gridLine), lineWidth: 1)
        }
    }
}

struct ConstructionBackground: ViewModifier {
    func body(content: Content) -> some View {
        ZStack {
            LinearGradient(
                colors: [
                    Color(red: 0.05, green: 0.06, blue: 0.06),
                    Color(red: 0.08, green: 0.10, blue: 0.09)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            BlueprintGrid()
                .ignoresSafeArea()

            content
        }
    }
}

extension View {
    func constructionBackground() -> some View {
        modifier(ConstructionBackground())
    }

    func constructionPanel() -> some View {
        padding(14)
            .background(ConstructPalette.card.opacity(0.94), in: RoundedRectangle(cornerRadius: 8))
            .overlay(RoundedRectangle(cornerRadius: 8).stroke(ConstructPalette.gridLine))
    }
}

struct SectionTitle: View {
    let title: String
    let symbol: String

    init(_ title: String, symbol: String) {
        self.title = title
        self.symbol = symbol
    }

    var body: some View {
        Label(title.uppercased(), systemImage: symbol)
            .font(.system(size: 12, weight: .heavy, design: .monospaced))
            .foregroundStyle(ConstructPalette.laserGreen)
    }
}

struct PrimaryConstructButton: View {
    let title: String
    let symbol: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack {
                Image(systemName: symbol)
                Text(title)
                    .fontWeight(.heavy)
                Spacer()
                Image(systemName: "arrow.up.right")
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
